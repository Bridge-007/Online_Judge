"""
Code Execution & Evaluation Engine — Subprocess Based.

Runs user-submitted code directly via subprocess with the compilers
installed in the Docker container (g++, javac, python3).
Compares output against test cases and returns a verdict.
Creates per-test-case result records.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time

from .models import TestCaseResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Startup: check which compilers are available
# ---------------------------------------------------------------------------

def _check_compiler(name):
    """Check if a compiler/runtime is available and log the result."""
    path = shutil.which(name)
    if path:
        logger.info("✓ %s found at %s", name, path)
    else:
        logger.warning("✗ %s NOT found in PATH", name)
    return path is not None

_COMPILERS_CHECKED = False

def _log_compiler_availability():
    """Log compiler availability once at startup."""
    global _COMPILERS_CHECKED
    if _COMPILERS_CHECKED:
        return
    _COMPILERS_CHECKED = True
    logger.info("=== Compiler availability check ===")
    _check_compiler('g++')
    _check_compiler('javac')
    _check_compiler('java')
    _check_compiler('python3')
    logger.info("=== End compiler check ===")


# ---------------------------------------------------------------------------
# Language Configuration
# ---------------------------------------------------------------------------

LANGUAGE_CONFIG = {
    'python': {
        'filename': 'main.py',
        'compile': None,
        'run': lambda d: [sys.executable, os.path.join(d, 'main.py')],
    },
    'cpp': {
        'filename': 'main.cpp',
        'compile': lambda d: ['g++', '-O2', os.path.join(d, 'main.cpp'), '-o', os.path.join(d, 'main.out')],
        'run': lambda d: [os.path.join(d, 'main.out')],
    },
    'java': {
        'filename': 'Main.java',
        'compile': lambda d: ['javac', os.path.join(d, 'Main.java')],
        'run': lambda d: ['java', '-cp', d, 'Main'],
    },
}


# ---------------------------------------------------------------------------
# Execution helper
# ---------------------------------------------------------------------------

def _run_subprocess(command_parts, sandbox_dir, timeout, stdin_data=None):
    """
    Run a command via subprocess with timeout.
    Returns (stdout, stderr, returncode, timed_out, exec_time).
    """
    start_time = time.time()
    try:
        proc = subprocess.run(
            command_parts,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=sandbox_dir,
        )
        exec_time = round(time.time() - start_time, 4)
        return proc.stdout, proc.stderr, proc.returncode, False, exec_time
    except subprocess.TimeoutExpired:
        exec_time = round(time.time() - start_time, 4)
        return '', 'Time Limit Exceeded', -1, True, exec_time
    except FileNotFoundError as e:
        logger.error("Compiler/runtime not found: %s", e)
        return '', f'Compiler/runtime not found: {e}', -1, False, 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_code(code, language, input_data, time_limit, memory_limit_mb=None):
    """
    Run user code against a single input. Returns a dict with:
        status, output, exec_time
    Used by both judge_submission (per test case) and run_custom_test.
    """
    config = LANGUAGE_CONFIG.get(language)
    if config is None:
        return {'status': 'Runtime Error', 'output': f'Unsupported language: {language}', 'exec_time': None}

    # Log compiler availability once (for debugging deployment issues)
    _log_compiler_availability()

    sandbox = tempfile.mkdtemp(prefix='oj_sandbox_')

    try:
        # Write code to file
        code_path = os.path.join(sandbox, config['filename'])
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # --- Compile (if needed) ---
        compile_fn = config['compile']
        if compile_fn is not None:
            compile_cmd = compile_fn(sandbox)
            stdout, stderr, rc, timed_out, _ = _run_subprocess(
                compile_cmd, sandbox, timeout=30,
            )
            if rc != 0:
                return {
                    'status': 'Compilation Error',
                    'output': stderr[:2000] if stderr else 'Compilation failed.',
                    'exec_time': None,
                }

        # --- Run ---
        run_cmd = config['run'](sandbox)
        stdout, stderr, rc, timed_out, exec_time = _run_subprocess(
            run_cmd, sandbox, timeout=time_limit, stdin_data=input_data,
        )

        if timed_out:
            return {'status': 'Time Limit Exceeded', 'output': 'Time Limit Exceeded.', 'exec_time': exec_time}

        if rc != 0:
            error_msg = stderr[:2000] if stderr else 'Non-zero exit code.'
            # Exit code 137 = OOM kill (SIGKILL from kernel)
            if rc == 137:
                return {'status': 'Memory Limit Exceeded', 'output': 'Memory Limit Exceeded.', 'exec_time': exec_time}
            return {'status': 'Runtime Error', 'output': error_msg, 'exec_time': exec_time}

        return {'status': 'ok', 'output': stdout.strip(), 'exec_time': exec_time}

    except Exception as exc:
        return {'status': 'Runtime Error', 'output': str(exc)[:2000], 'exec_time': None}
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def judge_submission(submission):
    """
    Evaluate a Submission against all of its problem's test cases.

    Creates a TestCaseResult row for every test case, then sets the overall
    submission.status and submission.output accordingly.
    """
    problem = submission.problem
    language = submission.language

    if language not in LANGUAGE_CONFIG:
        submission.status = 'Runtime Error'
        submission.output = f'Unsupported language: {language}'
        submission.save()
        return

    test_cases = list(problem.test_cases.all())
    if not test_cases:
        submission.status = 'Accepted'
        submission.output = 'No test cases defined — auto-accepted.'
        submission.save()
        return

    overall_status = 'Accepted'
    first_fail_msg = ''
    passed_count = 0

    for i, tc in enumerate(test_cases, start=1):
        result = run_code(
            code=submission.code,
            language=language,
            input_data=tc.input_data,
            time_limit=problem.time_limit,
            memory_limit_mb=problem.memory_limit,
        )

        tc_status = 'Passed'
        actual_output = result['output']
        exec_time = result['exec_time']

        if result['status'] != 'ok':
            tc_status = result['status']
        else:
            # Compare output
            expected = tc.expected_output.strip()
            if actual_output != expected:
                tc_status = 'Wrong Answer'

        # Save per-test-case result
        TestCaseResult.objects.create(
            submission=submission,
            test_case=tc,
            test_case_number=i,
            status=tc_status,
            actual_output=actual_output[:2000],
            execution_time=exec_time,
            memory_used=None,
        )

        if tc_status == 'Passed':
            passed_count += 1
        elif overall_status == 'Accepted':
            overall_status = tc_status
            first_fail_msg = f'{tc_status} on test case {i}.'

    # Set overall verdict
    total = len(test_cases)
    if overall_status == 'Accepted':
        submission.status = 'Accepted'
        submission.output = f'All {total} test case(s) passed.'
    else:
        submission.status = overall_status
        submission.output = f'Passed {passed_count}/{total} test case(s). {first_fail_msg}'
    submission.save()
