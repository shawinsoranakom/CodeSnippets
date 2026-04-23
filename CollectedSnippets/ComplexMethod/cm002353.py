def get_errors_from_single_artifact(artifact_zip_path, job_links=None):
    """Extract errors from a downloaded artifact (in .zip format)"""
    errors = []
    failed_tests = []
    job_name = None

    with zipfile.ZipFile(artifact_zip_path) as z:
        for filename in z.namelist():
            if not os.path.isdir(filename):
                # read the file
                if filename in ["failures_line.txt", "summary_short.txt", "job_name.txt"]:
                    with z.open(filename) as f:
                        for line in f:
                            line = line.decode("UTF-8").strip()
                            if filename == "failures_line.txt":
                                try:
                                    # `error_line` is the place where `error` occurs
                                    error_line = line[: line.index(": ")]
                                    error = line[line.index(": ") + len(": ") :]
                                    errors.append([error_line, error])
                                except Exception:
                                    # skip un-related lines that don't match the expected format
                                    logger.debug(f"Skipping unrelated line: {line}")
                            elif filename == "summary_short.txt" and line.startswith("FAILED "):
                                # `test` is the test method that failed
                                test = line[len("FAILED ") :]
                                failed_tests.append(test)
                            elif filename == "job_name.txt":
                                job_name = line

    if len(errors) != len(failed_tests):
        raise ValueError(
            f"`errors` and `failed_tests` should have the same number of elements. Got {len(errors)} for `errors` "
            f"and {len(failed_tests)} for `failed_tests` instead. The test reports in {artifact_zip_path} have some"
            " problem."
        )

    job_link = None
    if job_name and job_links:
        job_link = job_links.get(job_name, None)

    # A list with elements of the form (line of error, error, failed test)
    result = [x + [y] + [job_link] for x, y in zip(errors, failed_tests)]

    return result