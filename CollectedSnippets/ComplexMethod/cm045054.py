def default_tabulate(
    args: List[str],
    scorer: ScorerFunc = default_scorer,
    timer: TimerFunc = default_timer,
    exclude_dir_names: List[str] = EXCLUDE_DIR_NAMES,
) -> None:
    invocation_cmd = args[0]
    args = args[1:]

    warning = f"CAUTION: '{invocation_cmd}' is in early preview and is not thoroughly tested.\nPlease do not cite values from these calculations in academic work without first inspecting and verifying the results in the run logs yourself."

    # Prepare the argument parser
    parser = argparse.ArgumentParser(
        prog=invocation_cmd,
        description=f"{invocation_cmd} will tabulate the results of a previous run.",
    )

    parser.add_argument(
        "runlogs",
        help="The path where the run's logs are stored.",
    )
    parser.add_argument(
        "-c",
        "--csv",
        action="store_true",
        help="Output the results in CSV format.",
    )

    parser.add_argument(
        "-e", "--excel", help="Output the results in Excel format. Please specify a path for the Excel file.", type=str
    )

    parsed_args = parser.parse_args(args)
    runlogs: str = parsed_args.runlogs

    all_results: List[Dict[str, Any]] = list()
    max_instances = 0

    for task_id in sorted(
        os.listdir(runlogs),
        key=lambda s: os.path.getmtime(os.path.join(runlogs, s)),
    ):
        if task_id in exclude_dir_names:
            continue

        task_path = os.path.join(runlogs, task_id)

        if not os.path.isdir(task_path):
            continue

        # Collect the results vector
        results: Dict[str, Any] = {"Task Id": task_id}

        # Collect the results for each instance.
        instance_dirs = sorted(
            os.listdir(task_path),
            key=lambda s: os.path.getmtime(os.path.join(task_path, s)),
        )
        instances = [int(d) for d in instance_dirs if d.isdigit()]

        for instance in instances:
            instance_dir = os.path.join(task_path, str(instance))
            results[f"Trial {instance} Success"] = scorer(instance_dir)
            results[f"Trial {instance} Time"] = timer(instance_dir)

        max_instances = max(instances)

        # Buffer the results
        all_results.append(results)

    num_instances = max_instances + 1

    # Pad the results to max_instances
    for result in all_results:
        for i in range(num_instances):
            if f"Trial {i} Success" not in result:
                result[f"Trial {i} Success"] = None
            if f"Trial {i} Time" not in result:
                result[f"Trial {i} Time"] = None

    # Create dataframe from results.
    df = pd.DataFrame(all_results)

    if parsed_args.csv:
        # Print out the dataframe in CSV format
        print(df.to_csv(index=False))
        # Print out alpha-version warning
        sys.stderr.write("\n" + warning + "\n\n")
    else:
        # Tabulate the results.
        print(tb.tabulate(df, headers="keys", tablefmt="simple"))  # type: ignore

        def _check_true(x: Any) -> Any:
            if isinstance(x, pd.Series):
                return x.apply(lambda y: y is True)  # type: ignore
            else:
                return x is True

        def _check_false(x: Any) -> Any:
            if isinstance(x, pd.Series):
                return x.apply(lambda y: y is False)  # type: ignore
            else:
                return x is False

        # Aggregate statistics for all tasks for each trials.
        print("\nSummary Statistics\n")
        score_columns = ["Trial " + str(i) + " Success" for i in range(num_instances)]
        # Count the number of successes when the value is True.
        successes = df[score_columns].apply(_check_true).sum(axis=0)  # type: ignore
        # Count the number of failures when the value is False.
        failures: pd.Series = df[score_columns].apply(_check_false).sum(axis=0)  # type: ignore
        # Count the number of missing
        missings = df[score_columns].isna().sum(axis=0)  # type: ignore
        # Count the total number of instances
        totals = successes + failures + missings  # type: ignore
        # Calculate the average success rates
        avg_success_rates = successes / (successes + failures)  # type: ignore
        time_columns = ["Trial " + str(i) + " Time" for i in range(num_instances)]  # type: ignore
        # Count the total time of non-null values
        total_times = df[time_columns].sum(axis=0, skipna=True)  # type: ignore
        # Calculate the average time of non-null values
        avg_times = df[time_columns].mean(axis=0, skipna=True)  # type: ignore

        def _list(series: Any) -> List[Any]:
            # If iteraable, convert to list
            if hasattr(series, "__iter__") and not isinstance(series, str):
                return list(series)
            else:
                # If not iterable, return the series
                return [series]

        # Create a per-trial summary dataframe
        trial_df = pd.DataFrame(
            {
                "Successes": _list(successes),  # type: ignore
                "Failures": _list(failures),  # type: ignore
                "Missing": _list(missings),  # type: ignore
                "Total": _list(totals),  # type: ignore
                "Average Success Rate": _list(avg_success_rates),  # type: ignore
                "Average Time": _list(avg_times),  # type: ignore
                "Total Time": _list(total_times),  # type: ignore
            },
            index=[f"Trial {i}" for i in range(num_instances)],
        )
        # Print out the per-trial summary dataframe.
        print(tb.tabulate(trial_df, headers="keys", tablefmt="simple"))  # type: ignore

        # Aggregate statistics across tasks for all trials.
        # At least one success for each trial, averaged across tasks.
        average_at_least_one_success = df[score_columns].any(axis=1).mean(skipna=True)  # type: ignore
        # All successes for each trial
        average_all_successes = df[score_columns].all(axis=1).mean(skipna=True)  # type: ignore

        # Create a dataframe
        trial_aggregated_df = pd.DataFrame(
            {
                "At Least One Success": [average_at_least_one_success],  # type: ignore
                "All Successes": [average_all_successes],  # type: ignore
            },
            index=["Trial Aggregated"],
        )
        # Print out the trial-aggregated dataframe.
        print(tb.tabulate(trial_aggregated_df, headers="keys", tablefmt="simple"))  # type: ignore

        # Print out alpha-version warning
        sys.stderr.write("\n" + warning + "\n\n")