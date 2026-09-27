import streamlit as st
import py_compile
import tempfile
import os
import re
import importlib.util

from analyzer import analyze_code
from ai_fixer import generate_ai_fix
from verifier import verify_fix
from tester import run_tests


# ============================================================
# LOAD TEST GENERATOR
# ============================================================

# test-generator.py contains a hyphen, so it cannot be imported
# using a normal Python import statement.

TEST_GENERATOR_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test-generator.py"
)


def load_test_generator():
    """
    Dynamically load test-generator.py.
    """

    if not os.path.exists(TEST_GENERATOR_PATH):
        raise FileNotFoundError(
            "test-generator.py was not found."
        )

    spec = importlib.util.spec_from_file_location(
        "test_generator",
        TEST_GENERATOR_PATH
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            "Unable to load test-generator.py."
        )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CodeGuard",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

if "ai_results" not in st.session_state:
    st.session_state.ai_results = {}

if "analyzed_code" not in st.session_state:
    st.session_state.analyzed_code = ""

if "issues" not in st.session_state:
    st.session_state.issues = []

if "generated_tests" not in st.session_state:
    st.session_state.generated_tests = {}

if "verification_results" not in st.session_state:
    st.session_state.verification_results = {}

if "test_results" not in st.session_state:
    st.session_state.test_results = {}

if "fixed_codes" not in st.session_state:
    st.session_state.fixed_codes = {}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_corrected_code(ai_response):
    """
    Extract Python code from the CORRECTED CODE section
    returned by Gemini.

    The AI fixer is instructed to return:

    CORRECTED CODE:
    <python code>
    """

    if not ai_response:
        return ""

    marker = "CORRECTED CODE:"

    if marker not in ai_response:
        return ""

    code_part = ai_response.split(
        marker,
        1
    )[1].strip()

    # Remove markdown fences if Gemini adds them
    if code_part.startswith("```python"):
        code_part = code_part[len("```python"):].strip()

    elif code_part.startswith("```"):
        code_part = code_part[3:].strip()

    if code_part.endswith("```"):
        code_part = code_part[:-3].strip()

    return code_part


def create_test_file_for_tester(
    fixed_code,
    test_code
):
    """
    Creates a temporary Python module for the fixed code
    and a pytest file which imports that module.

    This is used by tester.py.
    """

    code_temp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    )

    code_temp.write(fixed_code)
    code_temp.close()

    code_file = code_temp.name

    module_name = os.path.splitext(
        os.path.basename(code_file)
    )[0]

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

    test_temp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix="_test.py",
        delete=False,
        encoding="utf-8"
    )

    test_temp.write(complete_test)
    test_temp.close()

    return code_file, test_temp.name


def cleanup_file(file_path):
    """
    Safely remove a temporary file.
    """

    if file_path:

        try:
            os.remove(file_path)

        except Exception:
            pass


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ CodeGuard")

st.subheader(
    "AI-Powered Code Quality Guard"
)

st.write(
    "Analyze Python code, detect potential bugs, "
    "get AI-powered fixes, generate automated tests, "
    "and verify the proposed fix."
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🛡️ CodeGuard")

    st.write(
        "CodeGuard helps developers identify potential "
        "Python code issues, generate AI-powered fixes, "
        "and verify those fixes using automated tests."
    )

    st.divider()

    st.markdown("### 🔧 Features")

    st.markdown(
        """
        - 🔍 Static Code Analysis
        - 🐛 Bug Detection
        - 🚦 Severity Classification
        - 🤖 AI Fix Suggestions
        - 🧪 Automated Test Generation
        - ✅ Fix Verification
        - 📊 Final Report
        """
    )

    st.divider()

    st.caption(
        "Powered by Python + Gemini AI + Pytest"
    )


# ============================================================
# FILE UPLOAD
# ============================================================

st.header("📂 Upload Python Code")

uploaded_file = st.file_uploader(
    "Choose a Python file",
    type=["py"]
)


# ============================================================
# CODE INPUT
# ============================================================

code = ""

if uploaded_file is not None:

    try:

        code = uploaded_file.read().decode(
            "utf-8"
        )

        st.success(
            f"✅ Loaded file: {uploaded_file.name}"
        )

    except Exception as e:

        st.error(
            f"❌ Unable to read file: {e}"
        )

else:

    st.info(
        "You can upload a Python file or paste your code below."
    )

    code = st.text_area(
        "Paste Python code here:",
        height=250,
        placeholder="""Example:

def divide(a, b):
    return a / b
"""
    )


# ============================================================
# CODE PREVIEW
# ============================================================

if code.strip():

    with st.expander("👀 View Uploaded Code"):

        st.code(
            code,
            language="python"
        )


# ============================================================
# ANALYZE BUTTON
# ============================================================

if st.button(
    "🔍 Analyze Code",
    type="primary",
    use_container_width=True
):

    if not code.strip():

        st.warning(
            "⚠️ Please upload or paste Python code first."
        )

    else:

        # Clear previous results
        st.session_state.ai_results = {}
        st.session_state.generated_tests = {}
        st.session_state.verification_results = {}
        st.session_state.test_results = {}
        st.session_state.fixed_codes = {}

        # Save current code
        st.session_state.analyzed_code = code

        # Run analyzer
        with st.spinner(
            "🔍 Analyzing your Python code..."
        ):

            try:

                issues = analyze_code(code)

                st.session_state.issues = issues

            except Exception as e:

                st.session_state.issues = []

                st.error(
                    f"❌ Analyzer error: {str(e)}"
                )


# ============================================================
# DISPLAY ANALYSIS RESULTS
# ============================================================

if st.session_state.analyzed_code:

    current_code = st.session_state.analyzed_code
    issues = st.session_state.issues

    st.divider()

    st.header("🔍 Code Analysis")


    # ========================================================
    # NO ISSUES
    # ========================================================

    if not issues:

        st.success(
            "✅ No potential issues detected."
        )


    # ========================================================
    # ISSUES FOUND
    # ========================================================

    else:

        st.warning(
            f"⚠️ {len(issues)} potential issue(s) detected."
        )

        st.divider()


        for i, issue in enumerate(issues):

            issue_number = i + 1


            # =================================================
            # ISSUE CARD
            # =================================================

            if issue.get("severity") == "High":

                st.error(
                    f"""
🔴 **HIGH SEVERITY — ISSUE {issue_number}**

**Line:** {issue.get("line")}

**Problem:** {issue.get("issue")}

**Explanation:**  
{issue.get("explanation")}
"""
                )

            else:

                st.warning(
                    f"""
🟡 **MEDIUM SEVERITY — ISSUE {issue_number}**

**Line:** {issue.get("line")}

**Problem:** {issue.get("issue")}

**Explanation:**  
{issue.get("explanation")}
"""
                )


            # =================================================
            # AI FIX BUTTON
            # =================================================

            button_clicked = st.button(
                f"🤖 Generate AI Fix for Issue {issue_number}",
                key=f"ai_fix_button_{issue_number}",
                use_container_width=True
            )


            if button_clicked:

                with st.spinner(
                    f"🤖 Gemini is analyzing Issue {issue_number}..."
                ):

                    try:

                        ai_response = generate_ai_fix(
                            current_code,
                            issue
                        )

                        st.session_state.ai_results[
                            issue_number
                        ] = ai_response

                        # Try to extract corrected code
                        fixed_code = extract_corrected_code(
                            ai_response
                        )

                        if fixed_code:

                            st.session_state.fixed_codes[
                                issue_number
                            ] = fixed_code

                    except Exception as e:

                        st.session_state.ai_results[
                            issue_number
                        ] = (
                            f"❌ Gemini AI Error:\n\n{str(e)}"
                        )


            # =================================================
            # SHOW AI RESULT
            # =================================================

            if issue_number in st.session_state.ai_results:

                st.subheader(
                    f"🤖 AI Fix Suggestion — Issue {issue_number}"
                )

                ai_response = st.session_state.ai_results[
                    issue_number
                ]

                st.markdown(
                    ai_response
                )


                # =================================================
                # FIXED CODE
                # =================================================

                fixed_code = st.session_state.fixed_codes.get(
                    issue_number,
                    ""
                )


                if fixed_code:

                    with st.expander(
                        "🛠️ View Corrected Python Code",
                        expanded=True
                    ):

                        st.code(
                            fixed_code,
                            language="python"
                        )


                    # =================================================
                    # GENERATE TEST BUTTON
                    # =================================================

                    generate_test_clicked = st.button(
                        f"🧪 Generate Test for Issue {issue_number}",
                        key=f"generate_test_{issue_number}",
                        use_container_width=True
                    )


                    if generate_test_clicked:

                        with st.spinner(
                            f"🧪 Generating pytest test for Issue {issue_number}..."
                        ):

                            try:

                                test_generator = (
                                    load_test_generator()
                                )

                                generated_test = (
                                    test_generator.generate_test(
                                        current_code,
                                        issue,
                                        fixed_code
                                    )
                                )

                                st.session_state.generated_tests[
                                    issue_number
                                ] = generated_test

                            except Exception as e:

                                st.error(
                                    f"❌ Test generation error: {str(e)}"
                                )


                # =================================================
                # SHOW GENERATED TEST
                # =================================================

                if issue_number in st.session_state.generated_tests:

                    st.subheader(
                        f"🧪 Generated Pytest — Issue {issue_number}"
                    )

                    generated_test = (
                        st.session_state.generated_tests[
                            issue_number
                        ]
                    )

                    st.code(
                        generated_test,
                        language="python"
                    )


                    # =================================================
                    # VERIFY FIX
                    # =================================================

                    verify_clicked = st.button(
                        f"✅ Verify AI Fix — Issue {issue_number}",
                        key=f"verify_fix_{issue_number}",
                        use_container_width=True
                    )


                    if verify_clicked:

                        with st.spinner(
                            f"🔬 Verifying the fix for Issue {issue_number}..."
                        ):

                            try:

                                verification = verify_fix(
                                    fixed_code,
                                    generated_test
                                )

                                st.session_state.verification_results[
                                    issue_number
                                ] = verification

                            except Exception as e:

                                st.session_state.verification_results[
                                    issue_number
                                ] = {
                                    "success": False,
                                    "output": "",
                                    "error": str(e)
                                }


                    # =================================================
                    # SHOW VERIFICATION RESULT
                    # =================================================

                    if issue_number in (
                        st.session_state.verification_results
                    ):

                        verification = (
                            st.session_state.verification_results[
                                issue_number
                            ]
                        )

                        st.subheader(
                            f"🔬 Verification Result — Issue {issue_number}"
                        )

                        if verification.get("success"):

                            st.success(
                                "✅ AI-generated fix passed the generated pytest test."
                            )

                        else:

                            st.error(
                                "❌ AI-generated fix did not pass verification."
                            )


                        if verification.get("output"):

                            with st.expander(
                                "📄 Pytest Output"
                            ):

                                st.code(
                                    verification["output"],
                                    language="text"
                                )


                        if verification.get("error"):

                            with st.expander(
                                "⚠️ Pytest Error"
                            ):

                                st.code(
                                    verification["error"],
                                    language="text"
                                )


                    # =================================================
                    # RUN TESTER.PY SEPARATELY
                    # =================================================

                    tester_clicked = st.button(
                        f"▶️ Run Generated Test with Tester — Issue {issue_number}",
                        key=f"run_tester_{issue_number}",
                        use_container_width=True
                    )


                    if tester_clicked:

                        temp_code_file = None
                        temp_test_file = None

                        with st.spinner(
                            f"▶️ Running pytest using tester.py for Issue {issue_number}..."
                        ):

                            try:

                                (
                                    temp_code_file,
                                    temp_test_file
                                ) = create_test_file_for_tester(
                                    fixed_code,
                                    generated_test
                                )

                                test_result = run_tests(
                                    temp_test_file
                                )

                                st.session_state.test_results[
                                    issue_number
                                ] = test_result

                            except Exception as e:

                                st.session_state.test_results[
                                    issue_number
                                ] = {
                                    "success": False,
                                    "output": "",
                                    "error": str(e)
                                }

                            finally:

                                cleanup_file(
                                    temp_test_file
                                )

                                cleanup_file(
                                    temp_code_file
                                )


                    # =================================================
                    # SHOW TESTER RESULT
                    # =================================================

                    if issue_number in st.session_state.test_results:

                        test_result = (
                            st.session_state.test_results[
                                issue_number
                            ]
                        )

                        st.subheader(
                            f"▶️ Tester Result — Issue {issue_number}"
                        )

                        if test_result.get("success"):

                            st.success(
                                "✅ tester.py executed the generated test successfully."
                            )

                        else:

                            st.error(
                                "❌ tester.py reported a test failure."
                            )


                        if test_result.get("output"):

                            st.code(
                                test_result["output"],
                                language="text"
                            )


                        if test_result.get("error"):

                            st.code(
                                test_result["error"],
                                language="text"
                            )


            st.divider()


    # ========================================================
    # ORIGINAL CODE SYNTAX VERIFICATION
    # ========================================================

    st.header("🧪 Original Code Syntax Verification")

    st.write(
        "CodeGuard checks whether the uploaded Python "
        "code can be successfully parsed and compiled."
    )


    temp_file_path = None

    try:

        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        )

        temp_file.write(current_code)
        temp_file.close()

        temp_file_path = temp_file.name


        py_compile.compile(
            temp_file_path,
            doraise=True
        )


        st.success(
            "✅ Python syntax verification passed."
        )

        st.write(
            "The uploaded code can be successfully "
            "parsed and compiled by Python."
        )


    except py_compile.PyCompileError as e:

        st.error(
            "❌ Python syntax verification failed."
        )

        st.code(
            str(e)
        )


    except Exception as e:

        st.error(
            f"❌ Verification error: {e}"
        )


    finally:

        cleanup_file(
            temp_file_path
        )


    # ========================================================
    # FINAL REPORT
    # ========================================================

    st.divider()

    st.header("📊 Final Report")


    high_count = sum(
        1
        for issue in issues
        if issue.get("severity") == "High"
    )

    medium_count = sum(
        1
        for issue in issues
        if issue.get("severity") == "Medium"
    )


    # ========================================================
    # METRICS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Issues Found",
            len(issues)
        )


    with col2:

        st.metric(
            "High Severity",
            high_count
        )


    with col3:

        st.metric(
            "Medium Severity",
            medium_count
        )


    with col4:

        verified_count = sum(
            1
            for result in (
                st.session_state.verification_results.values()
            )
            if result.get("success")
        )

        st.metric(
            "Verified Fixes",
            verified_count
        )


    # ========================================================
    # FINAL STATUS
    # ========================================================

    if issues:

        st.warning(
            "⚠️ Potential issues require developer attention."
        )

        st.write(
            "Use the AI Fix, Test Generation, and "
            "Verification buttons to validate proposed fixes."
        )

    else:

        st.success(
            "✅ CodeGuard did not detect any potential issues."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CodeGuard — AI-Powered Automated Code Analysis & Verification"
)
