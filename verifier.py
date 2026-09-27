import subprocess
import sys
import tempfile
import os


def verify_fix(fixed_code, test_code):
    """
    Runs the generated test against the fixed Python code.

    Returns:
        success: True/False
        output: pytest output
        error: error message
    """

    code_file = None
    test_file = None

    try:

        # ------------------------------------------------
        # Create temporary Python file for fixed code
        # ------------------------------------------------

        code_temp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        )

        code_temp.write(fixed_code)
        code_temp.close()

        code_file = code_temp.name

        # ------------------------------------------------
        # Get module name
        # ------------------------------------------------

        module_name = os.path.splitext(
            os.path.basename(code_file)
        )[0]

        # ------------------------------------------------
        # Add import statement to generated test
        # ------------------------------------------------

        complete_test = f"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(r"{code_file}")
)

from {module_name} import *

{test_code}
"""

        # ------------------------------------------------
        # Create temporary pytest file
        # ------------------------------------------------

        test_temp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix="_test.py",
            delete=False,
            encoding="utf-8"
        )

        test_temp.write(complete_test)
        test_temp.close()

        test_file = test_temp.name

        # ------------------------------------------------
        # Run pytest
        # ------------------------------------------------

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                test_file,
                "-v"
            ],
            capture_output=True,
            text=True
        )

        # ------------------------------------------------
        # Return result
        # ------------------------------------------------

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    except Exception as e:

        return {
            "success": False,
            "output": "",
            "error": str(e)
        }

    finally:

        # ------------------------------------------------
        # Cleanup temporary files
        # ------------------------------------------------

        if code_file:

            try:
                os.remove(code_file)
            except Exception:
                pass

        if test_file:

            try:
                os.remove(test_file)
            except Exception:
                pass