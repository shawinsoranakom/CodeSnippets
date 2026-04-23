def _gather_tunableop_results() -> None:
    r"""Gather results from multiple tunableop results file and create a single file."""
    gemm_lines = set()
    validator_lines = []

    # Need to allow for the possibility that results filename was
    # set with the Python API instead of with environment variable.
    # Also possible that results filename was not set at all.
    # There are several test cases to check, but ultimately we
    # need a glob-able expression
    results_filename = get_filename()  # Note empty string could be returned here

    if (
        results_filename is not None and results_filename != ""
    ):  # Case were the Python API was used to set the filename
        dot_pos = results_filename.find(".")
        if dot_pos != -1 and dot_pos > 0:
            # Replace the character just to the left of the dot
            filename_pattern = (
                results_filename[: dot_pos - 1] + "?" + results_filename[dot_pos:]
            )
        else:
            filename_pattern = ""  # Needed to make linter happy
    else:  # Case where the environment variable was used to set the filename.
        results_filename_env = os.getenv("PYTORCH_TUNABLEOP_FILENAME")
        if results_filename_env is None or results_filename_env == "":
            filename_pattern = "tunableop_results?.csv"
        elif "%d" in results_filename_env:
            filename_pattern = results_filename_env.replace("%d", "?")
        else:
            filename_pattern = results_filename_env.replace(".", "?.")

    if "?" not in filename_pattern:
        raise AssertionError(
            f"filename_pattern must contain '?', got {filename_pattern!r}"
        )

    FirstFile = False
    matching_files = glob.glob(filename_pattern)
    num_matching_files = len(matching_files)
    for file_path in matching_files:
        with open(file_path) as file:
            for line in file:
                if line.startswith("Validator"):
                    if not (FirstFile):
                        # Only read Validator from first file
                        validator_lines.append(line)
                else:
                    gemm_lines.add(line)

        FirstFile = True

    output_file = filename_pattern.replace("?", "_full0")

    with open(output_file, "w") as out_file:
        for line in validator_lines:
            out_file.write(line)
        for line in gemm_lines:
            out_file.write(line)

    # Create num_matching_copies of the results file
    for i in range(1, num_matching_files):
        duplicate_file = output_file.replace("0", str(i))
        shutil.copy(output_file, duplicate_file)