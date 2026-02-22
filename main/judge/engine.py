"""
Code Execution & Evaluation Engine — Docker Sandboxed.

Runs user-submitted code inside isolated Docker containers with strict
resource limits (CPU, memory, no network). Compares output against test
cases and returns a verdict. Creates per-test-case result records.
"""

import os
import shutil
import subprocess
import tempfile
import time

from .models import TestCaseResult

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SANDBOX_IMAGE = 'warcode-sandbox'

# Resource limits for the sandbox container
CONTAINER_MEMORY = '256m'
CONTAINER_CPUS = '0.5'

LANGUAGE_CONFIG = {
    'python': {
        'filename': 'main.py',
        'compile': None,
        'run': 'python3 /sandbox/main.py',
    },
    'cpp': {
        'filename': 'main.cpp',
        'compile': 'g++ /sandbox/main.cpp -o /sandbox/main.exe',
        'run': '/sandbox/main.exe',
    },
    'java': {
        'filename': 'Main.java',
        'compile': 'javac /sandbox/Main.java',
        'run': 'java -cp /sandbox Main',
    },
}


# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------

def _docker_available():
    """Check if Docker is available and the sandbox image exists."""
    try:
        result = subprocess.run(
            ['docker', 'image', 'inspect', SANDBOX_IMAGE],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_in_docker(command, sandbox_dir, timeout, stdin_data=None):
    """
    Execute a command inside a Docker container with strict limits.

    Returns (stdout, stderr, returncode, timed_out, exec_time).
    """
    docker_cmd = [
        'docker', 'run',
        '--rm',
        '--network', 'none',           # No internet access
        '--memory', CONTAINER_MEMORY,   # Memory limit
        '--cpus', CONTAINER_CPUS,       # CPU limit
        '--read-only',                  # Read-only root filesystem
        '--tmpfs', '/tmp:size=64m',     # Small writable /tmp
        '--user', 'sandbox',           # Non-root user
        '-v', f'{sandbox_dir}:/sandbox:rw',
        '-w', '/sandbox',
        SANDBOX_IMAGE,
        'bash', '-c', command,
    ]

    start_time = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            docker_cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout + 5,  # Extra 5s for Docker overhead
        )
        exec_time = round(time.time() - start_time, 4)
        return proc.stdout, proc.stderr, proc.returncode, False, exec_time
    except subprocess.TimeoutExpired:
        exec_time = round(time.time() - start_time, 4)
        return '', 'Time Limit Exceeded', -1, True, exec_time


def _run_locally(command_parts, sandbox_dir, timeout, stdin_data=None,
                 is_compile=False):
    """
    Fallback: run code locally using subprocess (when Docker is unavailable).
    Used for local development when Docker is not running.
    """
    start_time = time.time()
    try:
        proc = subprocess.run(
            command_parts,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout if not is_compile else 30,
            cwd=sandbox_dir,
        )
        exec_time = round(time.time() - start_time, 4)
        return proc.stdout, proc.stderr, proc.returncode, False, exec_time
    except subprocess.TimeoutExpired:
        exec_time = round(time.time() - start_time, 4)
        return '', 'Time Limit Exceeded', -1, True, exec_time
    except FileNotFoundError:
        return '', f'Compiler/runtime not found.', -1, False, 0


# Legacy local-run config (used when Docker is unavailable)
import sys

LOCAL_LANGUAGE_CONFIG = {
    'python': {
        'filename': 'main.py',
        'compile': None,
        'run': lambda d: [sys.executable, os.path.join(d, 'main.py')],
    },
    'cpp': {
        'filename': 'main.cpp',
        'compile': lambda d: ['g++', os.path.join(d, 'main.cpp'), '-o', os.path.join(d, 'main.exe')],
        'run': lambda d: [os.path.join(d, 'main.exe')],
    },
    'java': {
        'filename': 'Main.java',
        'compile': lambda d: ['javac', os.path.join(d, 'Main.java')],
        'run': lambda d: ['java', '-cp', d, 'Main'],
    },
}


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

    sandbox = tempfile.mkdtemp(prefix='oj_sandbox_')

    try:
        # Write code to file
        code_path = os.path.join(sandbox, config['filename'])
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(code)

        use_docker = _docker_available()

        # --- Compile (if needed) ---
        if config['compile'] is not None:
            if use_docker:
                stdout, stderr, rc, timed_out, _ = _run_in_docker(
                    config['compile'], sandbox, timeout=30,
                )
            else:
                local_cfg = LOCAL_LANGUAGE_CONFIG[language]
                compile_cmd = local_cfg['compile'](sandbox)
                stdout, stderr, rc, timed_out, _ = _run_locally(
                    compile_cmd, sandbox, timeout=30, is_compile=True,
                )

            if rc != 0:
                return {
                    'status': 'Compilation Error',
                    'output': stderr[:2000] if stderr else 'Compilation failed.',
                    'exec_time': None,
                }

        # --- Run ---
        if use_docker:
            stdout, stderr, rc, timed_out, exec_time = _run_in_docker(
                config['run'], sandbox, timeout=time_limit, stdin_data=input_data,
            )
        else:
            local_cfg = LOCAL_LANGUAGE_CONFIG[language]
            run_cmd = local_cfg['run'](sandbox)
            stdout, stderr, rc, timed_out, exec_time = _run_locally(
                run_cmd, sandbox, timeout=time_limit, stdin_data=input_data,
            )

        if timed_out:
            return {'status': 'Time Limit Exceeded', 'output': 'Time Limit Exceeded.', 'exec_time': exec_time}

        if rc != 0:
            error_msg = stderr[:2000] if stderr else 'Non-zero exit code.'
            # Docker returns exit code 137 for OOM kills
            if rc == 137:
                return {'status': 'Memory Limit Exceeded', 'output': 'Memory Limit Exceeded (killed by container).', 'exec_time': exec_time}
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

    Possible verdicts:
        - Accepted
        - Wrong Answer
        - Time Limit Exceeded
        - Runtime Error
        - Compilation Error
        - Memory Limit Exceeded
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
