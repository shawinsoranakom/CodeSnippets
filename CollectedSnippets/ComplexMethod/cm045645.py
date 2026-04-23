def test_randomly_sorted_different_streams():
    number_events = 10
    number_topics = 3

    timestamp_step = 100

    timestamp_array = []
    topic_array = []
    name_array = []

    for topic_index in range(number_topics):
        timestamp_array += [
            topic_index * (number_events * timestamp_step) + i * timestamp_step
            for i in range(number_events)
        ]
        topic_array += ["topic_" + str(topic_index) for i in range(number_events)]
        name_array += [
            "event_" + str(topic_index) + "_" + str(i) for i in range(number_events)
        ]
        # index_sorted += [
        #     topic_index * number_events + i + 1 for i in range(number_events)
        # ]

    index = [i + 1 for i in range(number_topics * number_events)]

    index_shuffled = [i + 1 for i in range(number_topics * number_events)]
    random.seed(0)
    random.shuffle(index_shuffled)
    timestamp_array_shuffled = [timestamp_array[i - 1] for i in index_shuffled]
    topic_array_shuffled = [topic_array[i - 1] for i in index_shuffled]
    name_array_shuffled = [name_array[i - 1] for i in index_shuffled]
    events_pandas = pd.DataFrame(
        {
            "timestamp": timestamp_array_shuffled,
            "topic_id": topic_array_shuffled,
            "name": name_array_shuffled,
        },
        index=index,
    )
    events = T(events_pandas, format="pandas")

    results_events, results_differences = get_differences(events)

    prev_array = []
    next_array = []

    for topic_index in range(number_topics):
        prev_array_aux = [topic_index * number_events + i for i in range(number_events)]
        prev_array_aux[0] = float("nan")
        prev_array += prev_array_aux
        next_array_aux = [
            topic_index * number_events + i + 2 for i in range(number_events)
        ]
        next_array_aux[-1] = float("nan")
        next_array += next_array_aux

    def get_shuffled_version(i, array):
        if math.isnan(array[i]):
            return array[i]
        else:
            return index_shuffled.index(int(array[i])) + 1

    prev_array_shuffled = [
        get_shuffled_version(i - 1, prev_array) for i in index_shuffled
    ]
    next_array_shuffled = [
        get_shuffled_version(i - 1, next_array) for i in index_shuffled
    ]

    expected_results_events_pandas = pd.DataFrame(
        {"key": index, "next": next_array_shuffled, "prev": prev_array_shuffled},
        index=index,
    )
    expected_results_events = T(expected_results_events_pandas, format="pandas")
    expected_results_events = convert_table(expected_results_events)
    assert_table_equality_wo_index(results_events, expected_results_events)

    delta_array = [timestamp_step for i in range(number_topics * (number_events - 1))]
    index_delta = []
    for topic in range(number_topics):
        index_delta += [topic * number_events + i for i in range(number_events - 1)]
    expected_results_differences_pandas = pd.DataFrame(
        {"delta": delta_array}, index=index_delta
    )
    expected_results_differences = T(
        expected_results_differences_pandas, format="pandas"
    )
    assert_table_equality_wo_index(results_differences, expected_results_differences)