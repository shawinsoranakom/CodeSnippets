def check_output_correctness(
    latest_input_file, input_path, output_path, interrupted_run=False
):
    input_word_counts = {}
    old_input_word_counts = {}
    new_file_lines = set()
    distinct_new_words = set()

    input_file_list = os.listdir(input_path)
    for processing_old_files in (True, False):
        for file in input_file_list:
            path = os.path.join(input_path, file)
            if not os.path.isfile(path):
                continue

            on_old_file = path != latest_input_file
            if on_old_file != processing_old_files:
                continue
            with open(path) as f:
                for row in f:
                    if not row.strip() or row.strip() == "*COMMIT*":
                        continue
                    json_payload = json.loads(row.strip())
                    word = json_payload["word"]
                    if word not in input_word_counts:
                        input_word_counts[word] = 0
                    input_word_counts[word] += 1

                    if on_old_file:
                        if word not in old_input_word_counts:
                            old_input_word_counts[word] = 0
                        old_input_word_counts[word] += 1
                    else:
                        new_file_lines.add((word, input_word_counts[word]))
                        distinct_new_words.add(word)

    print("  New file lines:", len(new_file_lines))

    n_rows = 0
    n_old_lines = 0
    output_word_counts = {}
    try:
        with open(output_path) as f:
            is_first_row = True
            word_column_index = None
            count_column_index = None
            diff_column_index = None
            for row in f:
                n_rows += 1
                if is_first_row:
                    column_names = row.strip().replace('"', "").split(",")
                    for col_idx, col_name in enumerate(column_names):
                        if col_name == "word":
                            word_column_index = col_idx
                        elif col_name == "count":
                            count_column_index = col_idx
                        elif col_name == "diff":
                            diff_column_index = col_idx
                    is_first_row = False
                    assert (
                        word_column_index is not None
                    ), "'word' is absent in CSV header"
                    assert (
                        count_column_index is not None
                    ), "'count' is absent in CSV header"
                    assert (
                        diff_column_index is not None
                    ), "'diff' is absent in CSV header"
                    continue

                assert word_column_index is not None
                assert count_column_index is not None
                assert diff_column_index is not None
                tokens = row.strip().replace('"', "").split(",")
                try:
                    word = tokens[word_column_index].strip('"')
                    count = int(tokens[count_column_index])
                    diff = int(tokens[diff_column_index])
                    output_word_counts[word] = int(count)
                except (IndexError, ValueError):
                    # line split in two chunks, one fsynced, another did not
                    print(f"Broken row: {row}")
                    print(f"Tokens: {tokens}")
                    print(
                        f"Indices (word, count, diff): {word_column_index}, {count_column_index}, {diff_column_index}"
                    )
                    if not interrupted_run:
                        raise

                if diff == 1:
                    if (word, count) not in new_file_lines:
                        n_old_lines += 1
                elif diff == -1:
                    new_line_update = (word, count) in new_file_lines
                    old_line_update = old_input_word_counts.get(word) == count
                    if not (new_line_update or old_line_update):
                        n_old_lines += 1
                else:
                    raise ValueError("Incorrect diff value: {diff}")
    except FileNotFoundError:
        if interrupted_run:
            return False
        raise

    assert len(input_word_counts) >= len(output_word_counts), (
        "There are some new words on the output. "
        + f"Input dict: {len(input_word_counts)} Output dict: {len(output_word_counts)}"
    )

    for word, output_count in output_word_counts.items():
        if interrupted_run:
            assert input_word_counts[word] >= output_count
        else:
            assert (
                input_word_counts[word] == output_count
            ), f"Word: {word} Output count: {output_count} Input count: {input_word_counts.get(word)}"

    if not interrupted_run:
        assert latest_input_file is None or n_old_lines < DEFAULT_INPUT_SIZE / 10, (
            f"Output contains too many old lines: {n_old_lines} while 1/10 of the input size "
            + f"is {DEFAULT_INPUT_SIZE / 10}"
        )
        assert n_rows >= len(
            distinct_new_words
        ), f"Output contains only {n_rows} lines, while there should be at least {len(distinct_new_words)}"

    print("  Total rows on the output:", n_rows)
    print("  Total old lines:", n_old_lines)

    return input_word_counts == output_word_counts