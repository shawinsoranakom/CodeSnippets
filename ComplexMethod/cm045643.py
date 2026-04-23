def test_already_sorted():
    number_events = 10

    topic_ID = "topic"
    timestamp = 0
    timestamp_step = 100

    timestamp_array = [timestamp + i * timestamp_step for i in range(number_events)]
    topic_array = [topic_ID for i in range(number_events)]
    name_array = ["event_" + str(i) for i in range(number_events)]
    index = [i + 1 for i in range(number_events)]

    events_pandas = pd.DataFrame(
        {"timestamp": timestamp_array, "topic_id": topic_array, "name": name_array},
        index=index,
    )
    events = T(events_pandas, format="pandas")

    results_events, results_differences = get_differences(events)

    prev_array = [i - 1 for i in index]
    prev_array[0] = float("nan")
    next_array = [i + 1 for i in index]
    next_array[-1] = float("nan")

    expected_results_events_pandas = pd.DataFrame(
        {"key": index, "next": next_array, "prev": prev_array}, index=index
    )
    expected_results_events = T(expected_results_events_pandas, format="pandas")
    expected_results_events = convert_table(expected_results_events)

    assert_table_equality_wo_index(results_events, expected_results_events)

    delta_array = [timestamp_step for i in range(number_events - 1)]
    expected_results_differences_pandas = pd.DataFrame({"delta": delta_array})
    expected_results_differences = T(
        expected_results_differences_pandas, format="pandas"
    )
    assert_table_equality_wo_index(results_differences, expected_results_differences)