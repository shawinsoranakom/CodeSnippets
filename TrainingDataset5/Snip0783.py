def mincost_tickets(days: list[int], costs: list[int]) -> int:
    if not isinstance(days, list) or not all(isinstance(day, int) for day in days):
        raise ValueError("The parameter days should be a list of integers")

    if len(costs) != 3 or not all(isinstance(cost, int) for cost in costs):
        raise ValueError("The parameter costs should be a list of three integers")

    if len(days) == 0:
        return 0

    if min(days) <= 0:
        raise ValueError("All days elements should be greater than 0")

    if max(days) >= 366:
        raise ValueError("All days elements should be less than 366")

    days_set = set(days)

    @functools.cache
    def dynamic_programming(index: int) -> int:
        if index > 365:
            return 0

        if index not in days_set:
            return dynamic_programming(index + 1)

        return min(
            costs[0] + dynamic_programming(index + 1),
            costs[1] + dynamic_programming(index + 7),
            costs[2] + dynamic_programming(index + 30),
        )

    return dynamic_programming(1)
