import subprocess
import sys


def run_tests(test_file):
    try:
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