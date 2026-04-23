def assert_split_into_time_groups(
    t0: api.CapturedStream,
    t1: api.CapturedStream,
    transform: Callable[[api.DataRow], tuple[Hashable, int]],
) -> None:
    result: list[tuple[Any, int]] = [transform(row) for row in t0]
    expected: list[tuple[Any, int]] = [transform(row) for row in t1]
    assert len(result) == len(expected)
    expected_counter = collections.Counter(row[0] for row in expected)
    for key, count in expected_counter.items():
        if count != 1:
            raise ValueError(
                "This utility function does not support cases where the count of (value, diff)"
                + f" pair is !=1, but the count of {key} is {count}."
            )
    result.sort()
    expected.sort()
    expected_to_result_time: dict[int, int] = {}
    for (res_val, res_time), (ex_val, ex_time) in zip(result, expected):
        assert res_val == ex_val
        if ex_time not in expected_to_result_time:
            expected_to_result_time[ex_time] = res_time
        if res_time != expected_to_result_time[ex_time]:
            raise AssertionError(
                f"Expected {res_val} to have time {expected_to_result_time[ex_time]}"
                + f" but it has time {res_time}."
            )