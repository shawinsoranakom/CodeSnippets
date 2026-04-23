def test_impact_of_file(filename: str) -> str:
    """Determine what class of impact this file has on test runs.

    Possible values:
        TORCH - torch python code
        CAFFE2 - caffe2 python code
        TEST - torch test code
        UNKNOWN - may affect all tests
        NONE - known to have no effect on test outcome
        CI - CI configuration files
    """
    parts = filename.split(os.sep)
    if parts[0] in [".jenkins", ".ci"]:
        return "CI"
    if parts[0] in ["docs", "scripts", "CODEOWNERS", "README.md"]:
        return "NONE"
    elif parts[0] == "torch":
        if parts[-1].endswith(".py") or parts[-1].endswith(".pyi"):
            return "TORCH"
    elif parts[0] == "caffe2":
        if parts[-1].endswith(".py") or parts[-1].endswith(".pyi"):
            return "CAFFE2"
    elif parts[0] == "test":
        if parts[-1].endswith(".py") or parts[-1].endswith(".pyi"):
            return "TEST"

    return "UNKNOWN"