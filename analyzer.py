import ast


def analyze_code(code):
    issues = []

    try:
        tree = ast.parse(code)

        for node in ast.walk(tree):

            # 1. Check division operations
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                issues.append({
                    "line": node.lineno,
                    "issue": "Possible division by zero",
                    "severity": "High",
                    "explanation": "The denominator may become zero and cause a crash."
                })

            # 2. Check list indexing
            if isinstance(node, ast.Subscript):
                issues.append({
                    "line": node.lineno,
                    "issue": "Possible invalid list index",
                    "severity": "Medium",
                    "explanation": "The index may be outside the valid range."
                })

            # 3. Check empty list average
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "len":
                    issues.append({
                        "line": node.lineno,
                        "issue": "Possible empty collection",
                        "severity": "Medium",
                        "explanation": "Using len() in a calculation may cause an error if the collection is empty."
                    })

        return issues

    except SyntaxError as e:
        return [{
            "line": e.lineno,
            "issue": "Syntax Error",
            "severity": "High",
            "explanation": str(e)
        }]