def simple_interest(
    principal: float, daily_interest_rate: float, days_between_payments: float
) -> float:
    if days_between_payments <= 0:
        raise ValueError("days_between_payments must be > 0")
    if daily_interest_rate < 0:
        raise ValueError("daily_interest_rate must be >= 0")
    if principal <= 0:
        raise ValueError("principal must be > 0")
    return principal * daily_interest_rate * days_between_payments
