from sample_code import divide, get_user, calculate_average


def test_divide():
    assert divide(10, 2) == 5


def test_get_user():
    users = ["Ali", "Sara", "Ahmed"]
    assert get_user(users, 1) == "Sara"


def test_average():
    numbers = [10, 20, 30]
    assert calculate_average(numbers) == 20

    
def test_divide_by_zero():
    divide(10, 0)