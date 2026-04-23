def process_statistics(
    client_metrics: list[RequestStats],
    warmup_percentages: list[float],
    test_params: dict,
    verbose: bool,
    gen_conv_args: GenConvArgs | None = None,
    excel_output: bool = False,
    warmup_runtime_sec: float | None = None,
) -> None:
    if len(client_metrics) == 0:
        logger.info("No samples to process")
        return

    logger.info(f"Processing {len(client_metrics)} samples...")

    raw_data = pd.DataFrame(client_metrics)

    if verbose:
        # Calculate the time between user turns in each conversation (in a new column)
        raw_data = raw_data.sort_values(by=["conversation_id", "start_time_ms"])
        raw_data["time_between_user_turns_sec"] = raw_data.groupby("conversation_id")[
            "start_time_ms"
        ].diff()

        # Convert milliseconds to seconds
        raw_data["time_between_user_turns_sec"] = (
            raw_data["time_between_user_turns_sec"] / 1000.0
        )

    # Final raw data should be sorted by time
    raw_data = raw_data.sort_values(by=["start_time_ms"])
    raw_data["end_time_ms"] = raw_data["start_time_ms"] + raw_data["latency_ms"]

    percentiles = [0.25, 0.5, 0.75, 0.9]

    # Add more percentiles if there are enough samples
    if len(raw_data) >= 100:
        percentiles.append(0.99)

    if len(raw_data) >= 1000:
        percentiles.append(0.999)

    if len(raw_data) >= 10000:
        percentiles.append(0.9999)

    # Set precision for numbers in the output text (the dataframes)
    pd.set_option("display.precision", 2)

    # Exclude parameters from RequestStats
    exclude = [
        "start_time_ms",
        "end_time_ms",
        "output_num_first_chunk_tokens",
        "approx_cached_percent",
        "conversation_id",
        "client_id",
    ]

    print(TEXT_SEPARATOR)
    print(f"{Color.YELLOW}Parameters:{Color.RESET}")
    for k, v in test_params.items():
        print(f"{k}={v}")

    # conversations generation parameters
    if gen_conv_args is not None:
        gen_params = {
            "text_files": ", ".join(gen_conv_args.text_files),
            "input_num_turns": str(gen_conv_args.input_num_turns),
            "input_common_prefix_num_tokens": str(
                gen_conv_args.input_common_prefix_num_tokens
            ),
            "input_prefix_num_tokens": str(gen_conv_args.input_prefix_num_tokens),
            "input_num_tokens": str(gen_conv_args.input_num_tokens),
            "output_num_tokens": str(gen_conv_args.output_num_tokens),
        }

        print(f"{Color.YELLOW}Conversations Generation Parameters:{Color.RESET}")
        for k, v in gen_params.items():
            print(f"{k}={v}")

    print(TEXT_SEPARATOR)

    params_list = []
    df_list = []
    for percent in warmup_percentages:
        # Select samples from the end (tail) of the dataframe
        warmup_count = int(percent * len(raw_data))
        tail_count = len(raw_data) - warmup_count
        if tail_count == 0:
            # No reason to process if the count of samples is zero
            break

        df = raw_data.tail(tail_count)

        # Runtime is the diff between the end of the last request
        # and the start of the first request
        runtime_sec = df["end_time_ms"].iloc[-1] - df["start_time_ms"].iloc[0]

        # Convert milliseconds to seconds
        runtime_sec = runtime_sec / 1000.0
        requests_per_sec = float(len(df)) / runtime_sec
        params = {
            "runtime_sec": runtime_sec,
            "requests_per_sec": requests_per_sec,
        }
        if warmup_runtime_sec is not None:
            params["warmup_runtime_sec"] = warmup_runtime_sec
            params["total_runtime_incl_warmup_sec"] = runtime_sec + warmup_runtime_sec

        # Generate a summary of relevant metrics (and drop irrelevant data)
        df = df.drop(columns=exclude).describe(percentiles=percentiles).transpose()

        # List for Excel file
        params_list.append(params)
        df_list.append(df)

        # Print the statistics summary
        if percent > 0 or len(warmup_percentages) > 1:
            print(
                f"{Color.YELLOW}Statistics summary "
                f"(assuming {percent:.0%} warmup samples):{Color.RESET}"
            )
        else:
            print(f"{Color.YELLOW}Statistics summary:{Color.RESET}")

        for k, v in params.items():
            if isinstance(v, float):
                print(f"{k} = {v:.3f}")
            else:
                print(f"{k} = {v}")
        print(TEXT_SEPARATOR)
        print(df)
        print(TEXT_SEPARATOR)

    if excel_output:
        prefix = f"statistics_{test_params['num_clients']}_clients"
        filename = get_filename_with_timestamp(prefix, "xlsx")

        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            startrow = 0
            test_params_df = pd.DataFrame([test_params])
            test_params_df.to_excel(
                writer, sheet_name="Summary", index=False, startrow=startrow
            )
            startrow += len(test_params_df) + 3

            if gen_conv_args is not None:
                gen_params_df = pd.DataFrame([gen_params])
                gen_params_df.to_excel(
                    writer, sheet_name="Summary", index=False, startrow=(startrow - 1)
                )
                startrow += len(gen_params_df) + 3

            for params, df_stats in zip(params_list, df_list):
                df_params = pd.DataFrame([params])
                df_params.to_excel(
                    writer, sheet_name="Summary", index=False, startrow=startrow
                )
                startrow += len(df_params) + 2
                df_stats.to_excel(
                    writer, sheet_name="Summary", index=True, startrow=startrow
                )
                startrow += len(df_stats) + 3

            raw_data.to_excel(writer, sheet_name="Raw data", index=False, startrow=0)

        logger.info(
            f"{Color.GREEN}Client metrics exported to file: {filename}{Color.RESET}"
        )