import os

from dotenv import load_dotenv
from google import genai


# Load API key from .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


def generate_test(code, issue, fixed_code=None):

    if not API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not found. "
            "Please check your .env file."
        )

    client = genai.Client(
        api_key=API_KEY
    )

    fixed_section = ""

    if fixed_code:
        fixed_section = f"""
FIXED CODE:
{fixed_code}
"""

    prompt = f"""
You are CodeGuard's automated test generator.

Your job is to create a focused pytest test that verifies
whether a detected Python bug has actually been fixed.

ORIGINAL PYTHON CODE:
{code}

DETECTED ISSUE:
Line: {issue.get("line")}
Issue: {issue.get("issue")}
Severity: {issue.get("severity")}
Explanation: {issue.get("explanation")}

{fixed_section}

Requirements:

1. Generate a pytest test specifically for this issue.
2. The test must target the detected bug.
3. If a fixed version is provided, the test should verify
   the expected behavior of the fixed version.
4. Do not create unrelated tests.
5. Return ONLY valid Python pytest code.
6. Do not use markdown code fences.
7. Do not include explanations.
8. The generated test must be executable.

The output should look like:

def test_example():
    ...
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    test_code = response.text.strip()

    # Remove markdown fences if Gemini adds them anyway
    if test_code.startswith("```python"):
        test_code = test_code[len("```python"):].strip()

    if test_code.startswith("```"):
        test_code = test_code[3:].strip()

    if test_code.endswith("```"):
        test_code = test_code[:-3].strip()

    return test_code