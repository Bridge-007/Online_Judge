"""
Code Execution & Evaluation Engine.

Runs user-submitted code in a temporary sandbox directory, compares output
against test cases, and returns a verdict. Creates per-test-case result records.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import threading
import time

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from .models import TestCaseResult

# Map language identifiers to file names, compile commands, and run commands.
LANGUAGE_CONFIG = {
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


def _monitor_memory(pid, peak_holder, stop_event):
    """Poll peak RSS of *pid* every 50 ms until *stop_event* is set."""
    if not HAS_PSUTIL:
        return
    try:
        proc = psutil.Process(pid)
        while not stop_event.is_set():
            try:
                mem = proc.memory_info().rss / (1024 * 1024)  # bytes → MB
                if mem > peak_holder[0]:
                    peak_holder[0] = mem
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            time.sleep(0.05)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass


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
    config = LANGUAGE_CONFIG.get(language)

    if config is None:
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

    # --- 1. Create sandbox ---
    sandbox = tempfile.mkdtemp(prefix='oj_sandbox_')

    try:
        # --- 2. Write code to file ---
        code_path = os.path.join(sandbox, config['filename'])
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(submission.code)

        # --- 3. Compile (if needed) ---
        if config['compile'] is not None:
            compile_cmd = config['compile'](sandbox)
            try:
                result = subprocess.run(
                    compile_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    submission.status = 'Compilation Error'
                    submission.output = result.stderr[:2000]
                    submission.save()
                    return
            except FileNotFoundError:
                submission.status = 'Compilation Error'
                submission.output = f'Compiler not found for {language}. Make sure the compiler is installed and on PATH.'
                submission.save()
                return

        # --- 4. Run against each test case ---
        run_cmd = config['run'](sandbox)
        memory_limit_mb = problem.memory_limit
        overall_status = 'Accepted'
        first_fail_msg = ''
        passed_count = 0

        for i, tc in enumerate(test_cases, start=1):
            tc_status = 'Passed'
            actual_output = ''
            exec_time = None
            peak_mem = 0.0

            try:
                start_time = time.time()

                # Use Popen so we can monitor memory
                proc = subprocess.Popen(
                    run_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # Start memory monitor thread
                peak_holder = [0.0]
                stop_event = threading.Event()
                mem_thread = threading.Thread(
                    target=_monitor_memory,
                    args=(proc.pid, peak_holder, stop_event),
                    daemon=True,
                )
                mem_thread.start()

                try:
                    stdout, stderr = proc.communicate(
                        input=tc.input_data,
                        timeout=problem.time_limit,
                    )
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate()
                    stop_event.set()
                    mem_thread.join(timeout=1)
                    tc_status = 'Time Limit Exceeded'
                    actual_output = f'Time Limit Exceeded on test case {i}.'
                else:
                    stop_event.set()
                    mem_thread.join(timeout=1)

                    exec_time = round(time.time() - start_time, 4)
                    peak_mem = round(peak_holder[0], 2)

                    # Check memory limit
                    if HAS_PSUTIL and memory_limit_mb and peak_mem > memory_limit_mb:
                        tc_status = 'Memory Limit Exceeded'
                        actual_output = f'Memory Limit Exceeded on test case {i} ({peak_mem:.1f} MB > {memory_limit_mb} MB).'
                    elif proc.returncode != 0:
                        tc_status = 'Runtime Error'
                        error_msg = stderr[:2000] if stderr else 'Non-zero exit code.'
                        actual_output = error_msg
                    else:
                        actual = stdout.strip()
                        expected = tc.expected_output.strip()
                        actual_output = actual

                        if actual != expected:
                            tc_status = 'Wrong Answer'

            except Exception as exc:
                tc_status = 'Runtime Error'
                actual_output = str(exc)[:2000]

            # Save per-test-case result
            TestCaseResult.objects.create(
                submission=submission,
                test_case=tc,
                test_case_number=i,
                status=tc_status,
                actual_output=actual_output[:2000],
                execution_time=exec_time,
                memory_used=peak_mem if peak_mem > 0 else None,
            )

            if tc_status == 'Passed':
                passed_count += 1
            elif overall_status == 'Accepted':
                # First failure determines overall status
                overall_status = tc_status
                first_fail_msg = f'{tc_status} on test case {i}.'

        # --- 5. Set overall verdict ---
        total = len(test_cases)
        if overall_status == 'Accepted':
            submission.status = 'Accepted'
            submission.output = f'All {total} test case(s) passed.'
        else:
            submission.status = overall_status
            submission.output = f'Passed {passed_count}/{total} test case(s). {first_fail_msg}'
        submission.save()

    finally:
        # --- 6. Cleanup ---
        shutil.rmtree(sandbox, ignore_errors=True)
