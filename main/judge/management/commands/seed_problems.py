"""
Management command to seed the database with sample competitive-programming
problems and their test cases.

Usage:  python manage.py seed_problems
"""

from django.core.management.base import BaseCommand
from judge.models import Problem, TestCase


PROBLEMS = [
    # ── Two Sum ──────────────────────────────────────────────────────
    {
        "title": "Two Sum",
        "difficulty": "Easy",
        "time_limit": 2.0,
        "description": (
            "Given an array of integers `nums` and an integer `target`, "
            "return the **indices** of the two numbers that add up to `target`.\n\n"
            "You may assume that each input has **exactly one solution**, and "
            "you may not use the same element twice.\n\n"
            "**Input format**\n"
            "- First line: space-separated integers (the array).\n"
            "- Second line: a single integer (the target).\n\n"
            "**Output format**\n"
            "- Two space-separated indices (0-based), smaller index first.\n\n"
            "**Example**\n"
            "```\nInput:\n2 7 11 15\n9\n\nOutput:\n0 1\n```"
        ),
        "test_cases": [
            {"input_data": "2 7 11 15\n9",  "expected_output": "0 1", "is_sample": True},
            {"input_data": "3 2 4\n6",       "expected_output": "1 2", "is_sample": True},
            {"input_data": "3 3\n6",         "expected_output": "0 1", "is_sample": False},
            {"input_data": "1 5 3 7 2\n9",   "expected_output": "1 3", "is_sample": False},
            {"input_data": "-1 -2 -3 -4 -5\n-8", "expected_output": "2 4", "is_sample": False},
        ],
    },

    # ── Fibonacci Number ─────────────────────────────────────────────
    {
        "title": "Fibonacci Number",
        "difficulty": "Easy",
        "time_limit": 2.0,
        "description": (
            "Given an integer `n`, return the **n-th Fibonacci number**.\n\n"
            "The Fibonacci sequence is defined as:\n"
            "- F(0) = 0\n"
            "- F(1) = 1\n"
            "- F(n) = F(n-1) + F(n-2)  for n > 1\n\n"
            "**Input format**\n"
            "- A single integer `n` (0 ≤ n ≤ 30).\n\n"
            "**Output format**\n"
            "- A single integer — the n-th Fibonacci number.\n\n"
            "**Example**\n"
            "```\nInput:\n6\n\nOutput:\n8\n```"
        ),
        "test_cases": [
            {"input_data": "0",  "expected_output": "0",     "is_sample": True},
            {"input_data": "1",  "expected_output": "1",     "is_sample": True},
            {"input_data": "6",  "expected_output": "8",     "is_sample": True},
            {"input_data": "10", "expected_output": "55",    "is_sample": False},
            {"input_data": "20", "expected_output": "6765",  "is_sample": False},
            {"input_data": "30", "expected_output": "832040","is_sample": False},
        ],
    },

    # ── Reverse a String ─────────────────────────────────────────────
    {
        "title": "Reverse a String",
        "difficulty": "Easy",
        "time_limit": 1.0,
        "description": (
            "Given a string `s`, return the string reversed.\n\n"
            "**Input format**\n"
            "- A single line containing the string.\n\n"
            "**Output format**\n"
            "- The reversed string.\n\n"
            "**Example**\n"
            "```\nInput:\nhello\n\nOutput:\nolleh\n```"
        ),
        "test_cases": [
            {"input_data": "hello",      "expected_output": "olleh",      "is_sample": True},
            {"input_data": "abcdef",     "expected_output": "fedcba",     "is_sample": True},
            {"input_data": "a",          "expected_output": "a",          "is_sample": False},
            {"input_data": "racecar",    "expected_output": "racecar",    "is_sample": False},
            {"input_data": "Hello World","expected_output": "dlroW olleH","is_sample": False},
        ],
    },

    # ── Maximum Sub-array Sum ────────────────────────────────────────
    {
        "title": "Maximum Sub-array Sum",
        "difficulty": "Medium",
        "time_limit": 2.0,
        "description": (
            "Given an integer array `nums`, find the contiguous sub-array "
            "(containing at least one number) which has the **largest sum** "
            "and return that sum.\n\n"
            "**Input format**\n"
            "- A single line of space-separated integers.\n\n"
            "**Output format**\n"
            "- A single integer — the maximum sub-array sum.\n\n"
            "**Example**\n"
            "```\nInput:\n-2 1 -3 4 -1 2 1 -5 4\n\nOutput:\n6\n```\n"
            "(The sub-array [4, -1, 2, 1] has the largest sum = 6.)"
        ),
        "test_cases": [
            {"input_data": "-2 1 -3 4 -1 2 1 -5 4", "expected_output": "6",  "is_sample": True},
            {"input_data": "1",                       "expected_output": "1",  "is_sample": True},
            {"input_data": "5 4 -1 7 8",              "expected_output": "23", "is_sample": False},
            {"input_data": "-1 -2 -3 -4",             "expected_output": "-1", "is_sample": False},
            {"input_data": "1 2 3 4 5",               "expected_output": "15", "is_sample": False},
        ],
    },

    # ── FizzBuzz ─────────────────────────────────────────────────────
    {
        "title": "FizzBuzz",
        "difficulty": "Easy",
        "time_limit": 2.0,
        "description": (
            "Given an integer `n`, print numbers from 1 to `n`, but:\n"
            "- for multiples of 3 print `Fizz`,\n"
            "- for multiples of 5 print `Buzz`,\n"
            "- for multiples of both 3 and 5 print `FizzBuzz`.\n\n"
            "**Input format**\n"
            "- A single integer `n` (1 ≤ n ≤ 100).\n\n"
            "**Output format**\n"
            "- Each value on its own line.\n\n"
            "**Example**\n"
            "```\nInput:\n5\n\nOutput:\n1\n2\nFizz\n4\nBuzz\n```"
        ),
        "test_cases": [
            {
                "input_data": "5",
                "expected_output": "1\n2\nFizz\n4\nBuzz",
                "is_sample": True,
            },
            {
                "input_data": "15",
                "expected_output": (
                    "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n"
                    "11\nFizz\n13\n14\nFizzBuzz"
                ),
                "is_sample": True,
            },
            {
                "input_data": "1",
                "expected_output": "1",
                "is_sample": False,
            },
            {
                "input_data": "3",
                "expected_output": "1\n2\nFizz",
                "is_sample": False,
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample problems and test cases."

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for data in PROBLEMS:
            if Problem.objects.filter(title=data["title"]).exists():
                self.stdout.write(self.style.WARNING(f'  [SKIP] Already exists: {data["title"]}'))
                skipped_count += 1
                continue

            problem = Problem.objects.create(
                title=data["title"],
                description=data["description"],
                difficulty=data["difficulty"],
                time_limit=data["time_limit"],
            )

            for tc in data["test_cases"]:
                TestCase.objects.create(
                    problem=problem,
                    input_data=tc["input_data"],
                    expected_output=tc["expected_output"],
                    is_sample=tc["is_sample"],
                )

            self.stdout.write(self.style.SUCCESS(
                f'  [OK] Created: {data["title"]} '
                f'({len(data["test_cases"])} test cases)'
            ))
            created_count += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done — {created_count} created, {skipped_count} skipped."
        ))
