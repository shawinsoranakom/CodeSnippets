def pay(hours_worked: float, pay_rate: float, hours: float = 40) -> float:
    assert isinstance(hours_worked, (float, int)), (
        "Parameter 'hours_worked' must be of type 'int' or 'float'"
    )
    assert isinstance(pay_rate, (float, int)), (
        "Parameter 'pay_rate' must be of type 'int' or 'float'"
    )
    assert isinstance(hours, (float, int)), (
        "Parameter 'hours' must be of type 'int' or 'float'"
    )

    normal_pay = hours_worked * pay_rate
    over_time = max(0, hours_worked - hours)
    over_time_pay = over_time * pay_rate / 2
    return normal_pay + over_time_pay
