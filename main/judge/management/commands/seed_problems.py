"""
Management command to seed the database with sample competitive-programming
problems and their test cases.

Usage:  python manage.py seed_problems
"""

from django.core.management.base import BaseCommand
from judge.models import Problem, Tag, TestCase


PROBLEMS = [
    # ── Two Sum ──────────────────────────────────────────────────────
    {
        "title": "Two Sum",
        "difficulty": "Easy",
        "time_limit": 2.0,
        "tags": ["Arrays", "Hash Table"],
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
        "tags": ["Dynamic Programming", "Math"],
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
        "tags": ["Strings"],
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
        "tags": ["Arrays", "Dynamic Programming", "Greedy"],
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
        "tags": ["Math", "Simulation"],
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

    # ── Palindrome Check ────────────────────────────────────────────
    {
        "title": "Palindrome Check",
        "difficulty": "Easy",
        "time_limit": 1.0,
        "tags": ["Strings"],
        "description": (
            "Given a string `s`, determine whether it is a **palindrome**.\n\n"
            "A palindrome reads the same forwards and backwards "
            "(case-sensitive, including spaces).\n\n"
            "**Input format**\n"
            "- A single line containing the string.\n\n"
            "**Output format**\n"
            "- Print `Yes` if the string is a palindrome, otherwise `No`.\n\n"
            "**Example**\n"
            "```\nInput:\nracecar\n\nOutput:\nYes\n```"
        ),
        "test_cases": [
            {"input_data": "racecar",   "expected_output": "Yes", "is_sample": True},
            {"input_data": "hello",     "expected_output": "No",  "is_sample": True},
            {"input_data": "a",         "expected_output": "Yes", "is_sample": False},
            {"input_data": "abba",      "expected_output": "Yes", "is_sample": False},
            {"input_data": "ab",        "expected_output": "No",  "is_sample": False},
        ],
    },

    # ── Merge Two Sorted Arrays ─────────────────────────────────────
    {
        "title": "Merge Two Sorted Arrays",
        "difficulty": "Easy",
        "time_limit": 2.0,
        "tags": ["Arrays", "Sorting"],
        "description": (
            "Given two sorted integer arrays, merge them into a single "
            "**sorted** array.\n\n"
            "**Input format**\n"
            "- First line: space-separated integers of the first array.\n"
            "- Second line: space-separated integers of the second array.\n\n"
            "**Output format**\n"
            "- A single line of space-separated integers — the merged sorted array.\n\n"
            "**Example**\n"
            "```\nInput:\n1 3 5\n2 4 6\n\nOutput:\n1 2 3 4 5 6\n```"
        ),
        "test_cases": [
            {"input_data": "1 3 5\n2 4 6",     "expected_output": "1 2 3 4 5 6",     "is_sample": True},
            {"input_data": "1 2 3\n4 5 6",     "expected_output": "1 2 3 4 5 6",     "is_sample": True},
            {"input_data": "1\n2",              "expected_output": "1 2",              "is_sample": False},
            {"input_data": "1 1 1\n1 1 1",     "expected_output": "1 1 1 1 1 1",     "is_sample": False},
            {"input_data": "10 20\n5 15 25",   "expected_output": "5 10 15 20 25",   "is_sample": False},
        ],
    },

    # ── Valid Parentheses ───────────────────────────────────────────
    {
        "title": "Valid Parentheses",
        "difficulty": "Medium",
        "time_limit": 1.0,
        "tags": ["Strings", "Stack"],
        "description": (
            "Given a string `s` containing just the characters "
            "`(`, `)`, `{`, `}`, `[` and `]`, determine if the input "
            "string is **valid**.\n\n"
            "A string is valid if:\n"
            "1. Open brackets are closed by the same type of brackets.\n"
            "2. Open brackets are closed in the correct order.\n\n"
            "**Input format**\n"
            "- A single line containing the bracket string.\n\n"
            "**Output format**\n"
            "- Print `Yes` if valid, otherwise `No`.\n\n"
            "**Example**\n"
            "```\nInput:\n()[]{}\n\nOutput:\nYes\n```"
        ),
        "test_cases": [
            {"input_data": "()[]{}",   "expected_output": "Yes", "is_sample": True},
            {"input_data": "(]",       "expected_output": "No",  "is_sample": True},
            {"input_data": "{[]}",     "expected_output": "Yes", "is_sample": False},
            {"input_data": "([)]",     "expected_output": "No",  "is_sample": False},
            {"input_data": "",         "expected_output": "Yes", "is_sample": False},
            {"input_data": "((()))",   "expected_output": "Yes", "is_sample": False},
        ],
    },

    # ── Longest Common Subsequence ──────────────────────────────────
    {
        "title": "Longest Common Subsequence",
        "difficulty": "Medium",
        "time_limit": 2.0,
        "tags": ["Strings", "Dynamic Programming"],
        "description": (
            "Given two strings `s1` and `s2`, return the **length** of "
            "their longest common subsequence (LCS).\n\n"
            "A subsequence is a sequence derived from another sequence "
            "by deleting some or no elements without changing the order "
            "of the remaining elements.\n\n"
            "**Input format**\n"
            "- First line: string `s1`.\n"
            "- Second line: string `s2`.\n\n"
            "**Output format**\n"
            "- A single integer — the length of the LCS.\n\n"
            "**Example**\n"
            "```\nInput:\nabcde\nace\n\nOutput:\n3\n```"
        ),
        "test_cases": [
            {"input_data": "abcde\nace",     "expected_output": "3", "is_sample": True},
            {"input_data": "abc\nabc",       "expected_output": "3", "is_sample": True},
            {"input_data": "abc\ndef",       "expected_output": "0", "is_sample": False},
            {"input_data": "abcdef\nacf",    "expected_output": "3", "is_sample": False},
            {"input_data": "a\na",           "expected_output": "1", "is_sample": False},
        ],
    },

    # ── Binary Search ───────────────────────────────────────────────
    {
        "title": "Binary Search",
        "difficulty": "Easy",
        "time_limit": 1.0,
        "tags": ["Arrays"],
        "description": (
            "Given a **sorted** array of integers and a target value, "
            "return the **index** of the target if found, or `-1` if "
            "not present.\n\n"
            "**Input format**\n"
            "- First line: space-separated sorted integers.\n"
            "- Second line: a single integer (the target).\n\n"
            "**Output format**\n"
            "- A single integer — the 0-based index, or -1.\n\n"
            "**Example**\n"
            "```\nInput:\n1 3 5 7 9\n5\n\nOutput:\n2\n```"
        ),
        "test_cases": [
            {"input_data": "1 3 5 7 9\n5",     "expected_output": "2",  "is_sample": True},
            {"input_data": "1 3 5 7 9\n6",     "expected_output": "-1", "is_sample": True},
            {"input_data": "2 4 6 8 10\n2",    "expected_output": "0",  "is_sample": False},
            {"input_data": "2 4 6 8 10\n10",   "expected_output": "4",  "is_sample": False},
            {"input_data": "1\n1",              "expected_output": "0",  "is_sample": False},
        ],
    },

    # ── Count Inversions ────────────────────────────────────────────
    {
        "title": "Count Inversions",
        "difficulty": "Hard",
        "time_limit": 3.0,
        "tags": ["Arrays", "Sorting", "Divide and Conquer"],
        "description": (
            "Given an array of integers, count the number of **inversions**. "
            "An inversion is a pair of indices `(i, j)` such that "
            "`i < j` and `arr[i] > arr[j]`.\n\n"
            "**Input format**\n"
            "- A single line of space-separated integers.\n\n"
            "**Output format**\n"
            "- A single integer — the number of inversions.\n\n"
            "**Example**\n"
            "```\nInput:\n2 4 1 3 5\n\nOutput:\n3\n```\n"
            "(Inversions: (2,1), (4,1), (4,3))"
        ),
        "test_cases": [
            {"input_data": "2 4 1 3 5", "expected_output": "3",  "is_sample": True},
            {"input_data": "1 2 3 4 5", "expected_output": "0",  "is_sample": True},
            {"input_data": "5 4 3 2 1", "expected_output": "10", "is_sample": False},
            {"input_data": "1 3 2 4",   "expected_output": "1",  "is_sample": False},
            {"input_data": "1",          "expected_output": "0",  "is_sample": False},
        ],
    },

    # ── N-Queens ────────────────────────────────────────────────────
    {
        "title": "N-Queens",
        "difficulty": "Hard",
        "time_limit": 5.0,
        "tags": ["Backtracking"],
        "description": (
            "Given an integer `n`, return the **number of distinct solutions** "
            "to the N-Queens puzzle.\n\n"
            "The N-Queens puzzle asks you to place `n` queens on an "
            "`n x n` chessboard so that no two queens threaten each other "
            "(no two queens share the same row, column, or diagonal).\n\n"
            "**Input format**\n"
            "- A single integer `n` (1 <= n <= 10).\n\n"
            "**Output format**\n"
            "- A single integer — the number of solutions.\n\n"
            "**Example**\n"
            "```\nInput:\n4\n\nOutput:\n2\n```"
        ),
        "test_cases": [
            {"input_data": "4",  "expected_output": "2",     "is_sample": True},
            {"input_data": "1",  "expected_output": "1",     "is_sample": True},
            {"input_data": "8",  "expected_output": "92",    "is_sample": False},
            {"input_data": "5",  "expected_output": "10",    "is_sample": False},
            {"input_data": "6",  "expected_output": "4",     "is_sample": False},
        ],
    },

    # ── Climbing Stairs ─────────────────────────────────────────────
    {
        "title": "Climbing Stairs",
        "difficulty": "Easy",
        "time_limit": 1.0,
        "tags": ["Dynamic Programming", "Math"],
        "description": (
            "You are climbing a staircase. It takes `n` steps to reach the top. "
            "Each time you can climb **1 or 2** steps. In how many distinct "
            "ways can you climb to the top?\n\n"
            "**Input format**\n"
            "- A single integer `n` (1 <= n <= 45).\n\n"
            "**Output format**\n"
            "- A single integer — the number of distinct ways.\n\n"
            "**Example**\n"
            "```\nInput:\n3\n\nOutput:\n3\n```\n"
            "(Explanation: 1+1+1, 1+2, 2+1)"
        ),
        "test_cases": [
            {"input_data": "2",  "expected_output": "2",          "is_sample": True},
            {"input_data": "3",  "expected_output": "3",          "is_sample": True},
            {"input_data": "1",  "expected_output": "1",          "is_sample": False},
            {"input_data": "10", "expected_output": "89",         "is_sample": False},
            {"input_data": "20", "expected_output": "10946",      "is_sample": False},
            {"input_data": "45", "expected_output": "1836311903", "is_sample": False},
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

            # Assign tags
            for tag_name in data.get("tags", []):
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                problem.tags.add(tag)

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
