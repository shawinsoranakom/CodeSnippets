def enforce_single_aws_marker(items: list[pytest.Item]):
    """Enforce that each test has exactly one aws compatibility marker"""
    marker_errors = []

    for item in items:
        # we should only concern ourselves with tests in tests/aws/
        if "tests/aws" not in item.fspath.dirname:
            continue

        aws_markers = []
        for mark in item.iter_markers():
            if mark.name.startswith("aws_"):
                aws_markers.append(mark.name)

        if len(aws_markers) > 1:
            marker_errors.append(f"{item.nodeid}: Too many aws markers specified: {aws_markers}")
        elif len(aws_markers) == 0:
            marker_errors.append(
                f"{item.nodeid}: Missing aws marker. Specify at least one marker, e.g. @markers.aws.validated"
            )

    if marker_errors:
        raise pytest.UsageError(*marker_errors)