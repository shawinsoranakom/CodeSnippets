def equated_monthly_installments(
    principal: float, rate_per_annum: float, years_to_repay: int
) -> float:
    if principal <= 0:
        raise Exception("Principal borrowed must be > 0")
    if rate_per_annum < 0:
        raise Exception("Rate of interest must be >= 0")
    if years_to_repay <= 0 or not isinstance(years_to_repay, int):
        raise Exception("Years to repay must be an integer > 0")

    rate_per_month = rate_per_annum / 12

    number_of_payments = years_to_repay * 12

    return (
        principal
        * rate_per_month
        * (1 + rate_per_month) ** number_of_payments
        / ((1 + rate_per_month) ** number_of_payments - 1)
    )
