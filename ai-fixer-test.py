def generate_fix(issue):
    if issue["issue"] == "Possible division by zero":
        return """if b == 0:
    return 0
return a / b"""

    elif issue["issue"] == "Possible invalid list index":
        return """if 0 <= index < len(users):
    return users[index]
return None"""

    elif issue["issue"] == "Possible empty collection":
        return """if not numbers:
    return 0
return sum(numbers) / len(numbers)"""

    else:
        return "No automatic fix available for this issue."