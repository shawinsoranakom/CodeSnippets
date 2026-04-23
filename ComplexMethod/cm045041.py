def process_logs(logs_path, single_benchmark=False):
    """
    logs_path: str, path to the logs directory, containing subdirectories for each benchmark subset
    returns: pandas DataFrame with all the logs processed
    """
    # check if logs_path exists
    if not os.path.exists(logs_path):
        raise FileNotFoundError(
            f"Path {logs_path} does not exist, need to download logs, extract them into one common folder"
        )
    if single_benchmark:
        # subset should be a list with single folder which is the last part of the path
        subsets = [logs_path.split("/")[-1]]
        logs_path = "/".join(logs_path.split("/")[:-1])

    else:
        subsets = os.listdir(logs_path)
    results = []
    for subset in subsets:
        # check if folder is not empty
        if not os.listdir(os.path.join(logs_path, subset)) or subset == ".DS_Store" or subset == "__MACOSX":
            continue
        benchmark_name = subset.split("_")[0]
        instances = [
            f
            for f in os.listdir(os.path.join(logs_path, subset))
            if os.path.isdir(os.path.join(logs_path, subset, f))
            and os.path.exists(os.path.join(logs_path, subset, f, "0"))
        ]
        logging.info(f"Processing {subset} with {len(instances)} instances")
        for instance in instances:
            instance_dir_path = os.path.join(logs_path, subset, instance, "0")
            try:
                correct, expected_answer, final_answer = scorer(instance_dir_path, benchmark_name)
            except Exception as e:
                logging.error(f"Error processing {instance_dir_path}: {e}")
                continue
            messages = get_message_logs(instance_dir_path)
            results.append(
                {
                    "benchmark": benchmark_name,
                    "subset_benchmark": subset,
                    "instance": instance,
                    "task_information": get_task_information(instance_dir_path, benchmark_name),
                    "expected_answer": expected_answer,
                    "final_answer": final_answer,
                    "correct": correct,
                    "stalled": did_agent_stall(instance_dir_path),
                    "num_messages": len(messages),
                    "messages": messages,
                    "progress_not_being_made": is_progress_not_being_made(instance_dir_path),
                }
            )
    df_logs = pd.DataFrame(results)
    return df_logs