def straight_line_depreciation(
    useful_years: int,
    purchase_value: float,
    residual_value: float = 0.0,
) -> list[float]:

    if not isinstance(useful_years, int):
        raise TypeError("Useful years must be an integer")

    if useful_years < 1:
        raise ValueError("Useful years cannot be less than 1")

    if not isinstance(purchase_value, (float, int)):
        raise TypeError("Purchase value must be numeric")

    if not isinstance(residual_value, (float, int)):
        raise TypeError("Residual value must be numeric")

    if purchase_value < 0.0:
        raise ValueError("Purchase value cannot be less than zero")

    if purchase_value < residual_value:
        raise ValueError("Purchase value cannot be less than residual value")

    depreciable_cost = purchase_value - residual_value
    annual_depreciation_expense = depreciable_cost / useful_years

    list_of_depreciation_expenses = []
    accumulated_depreciation_expense = 0.0
    for period in range(useful_years):
        if period != useful_years - 1:
            accumulated_depreciation_expense += annual_depreciation_expense
            list_of_depreciation_expenses.append(annual_depreciation_expense)
        else:
            depreciation_expense_in_end_year = (
                depreciable_cost - accumulated_depreciation_expense
            )
            list_of_depreciation_expenses.append(depreciation_expense_in_end_year)

    return list_of_depreciation_expenses
