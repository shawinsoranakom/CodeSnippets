def scorer(instance_dir, benchmark_name):
    """
    Returns results based on the benchmark name and the instance directory.

    benchmark_name: str, the name of the benchmark, either "gaia" or "webarena"
    instance_dir: str, path to the instance directory
    returns: tuple, (bool, str, str) or None, depending on the benchmark
    """

    if benchmark_name == "gaia" or benchmark_name == "assistant":
        # Read the expected answer
        expected_answer_file = os.path.join(instance_dir, "expected_answer.txt")
        if not os.path.isfile(expected_answer_file):
            return None

        with open(expected_answer_file, "rt") as fh:
            expected_answer = fh.read().strip()

        # Read the console log
        console_log_file = os.path.join(instance_dir, "console_log.txt")
        if not os.path.isfile(console_log_file):
            return None

        with open(console_log_file, "rt") as fh:
            console_log = fh.read()
            final_answer = None
            m = re.search(r"FINAL ANSWER:(.*?)\n", console_log, re.DOTALL)
            if m:
                final_answer = m.group(1).strip()

            if final_answer is None:
                return None
            not_normalized_final = final_answer

            n_ex = normalize_answer(expected_answer)
            n_final = normalize_answer(final_answer)
            return (n_ex != "" and n_ex == n_final), n_ex, not_normalized_final

    elif benchmark_name == "webarena":
        # Read the console log
        console_log_file = os.path.join(instance_dir, "console_log.txt")
        if not os.path.isfile(console_log_file):
            return None

        with open(console_log_file, "rt") as fh:
            console_log = fh.read()
            final_score = None
            m = re.search(r"FINAL SCORE:(.*?)\n", console_log, re.DOTALL)
            if m:
                final_score = m.group(1).strip()

            if final_score is None:
                return None
            else:
                return float(final_score) > 0, "", ""

    else:
        raise ValueError(f"Unsupported benchmark_name: {benchmark_name}")