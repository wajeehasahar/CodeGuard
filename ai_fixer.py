import os

from dotenv import load_dotenv
from google import genai


# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


def generate_ai_fix(code, issue):

    if not API_KEY:
        return (
            "GEMINI_API_KEY was not found.\n\n"
            "Please check your .env file."
        )

    try:

        client = genai.Client(
            api_key=API_KEY
        )

        prompt = f"""
You are CodeGuard, an AI-powered Python code reviewer.

Analyze the following Python code.

PYTHON CODE:
{code}

DETECTED ISSUE:
Line: {issue.get("line")}
Issue: {issue.get("issue")}
Severity: {issue.get("severity")}
Explanation: {issue.get("explanation")}

Your task:

1. Explain the problem in simple language.
2. Explain why it can cause an error or crash.
3. Provide a practical recommended fix.
4. Provide corrected Python code.

Keep the response concise and useful.

Use this format:

PROBLEM:
Explain the problem.

WHY IT HAPPENS:
Explain the cause.

RECOMMENDED FIX:
Explain what should be changed.

CORRECTED CODE:
Provide the corrected Python code.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        return f"Gemini AI Error: {str(e)}"