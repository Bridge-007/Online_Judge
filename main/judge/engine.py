"""
Code Execution & Evaluation Engine.

Runs user-submitted code in a temporary sandbox directory, compares output
against test cases, and returns a verdict.
"""

import os
import sys
import shutil
import subprocess
import tempfile


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


def judge_submission(submission):
    """
    Evaluate a Submission against all of its problem's test cases.

    Updates submission.status and submission.output in-place, then saves.

    Possible verdicts:
        - Accepted
        - Wrong Answer
        - Time Limit Exceeded
        - Runtime Error
        - Compilation Error
    """
    problem = submission.problem
    language = submission.language
    config = LANGUAGE_CONFIG.get(language)

    if config is None:
        submission.status = 'Runtime Error'
        submission.output = f'Unsupported language: {language}'
        submission.save()
        return

    test_cases = problem.test_cases.all()
    if not test_cases.exists():
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

        for i, tc in enumerate(test_cases, start=1):
            try:
                result = subprocess.run(
                    run_cmd,
                    input=tc.input_data,
                    capture_output=True,
                    text=True,
                    timeout=problem.time_limit,
                )
            except subprocess.TimeoutExpired:
                submission.status = 'Time Limit Exceeded'
                submission.output = f'Time Limit Exceeded on test case {i}.'
                submission.save()
                return

            # Runtime Error?
            if result.returncode != 0:
                submission.status = 'Runtime Error'
                error_msg = result.stderr[:2000] if result.stderr else 'Non-zero exit code.'
                submission.output = f'Runtime Error on test case {i}:\n{error_msg}'
                submission.save()
                return

            # Compare output (strip trailing whitespace per line, then compare)
            actual = result.stdout.strip()
            expected = tc.expected_output.strip()

            if actual != expected:
                submission.status = 'Wrong Answer'
                submission.output = (
                    f'Wrong Answer on test case {i}.\n'
                    f'Expected:\n{expected[:500]}\n\n'
                    f'Got:\n{actual[:500]}'
                )
                submission.save()
                return

        # All test cases passed
        submission.status = 'Accepted'
        submission.output = f'All {test_cases.count()} test case(s) passed.'
        submission.save()

    finally:
        # --- 5. Cleanup ---
        shutil.rmtree(sandbox, ignore_errors=True)
