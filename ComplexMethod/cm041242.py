def filter_by_markers(config: "Config", items: list[pytest.Item]):
    """Filter tests by markers."""
    from localstack import config as localstack_config
    from localstack.utils.bootstrap import in_ci
    from localstack.utils.platform import Arch, get_arch

    is_offline = config.getoption("--offline")
    is_in_docker = localstack_config.is_in_docker
    is_in_ci = in_ci()
    is_amd64 = get_arch() == Arch.amd64
    is_arm64 = get_arch() == Arch.arm64
    # Inlining `is_aws_cloud()` here because localstack.testing.aws.util imports boto3,
    # which is not installed for the CLI tests
    is_real_aws = os.environ.get("TEST_TARGET", "") == "AWS_CLOUD"

    if is_real_aws:
        # Do not skip any tests if they are executed against real AWS
        return

    skip_offline = pytest.mark.skip(
        reason="Test cannot be executed offline / in a restricted network environment. "
        "Add network connectivity and remove the --offline option when running "
        "the test."
    )
    requires_in_container = pytest.mark.skip(
        reason="Test requires execution inside a container (e.g., to install system packages)"
    )
    only_on_amd64 = pytest.mark.skip(
        reason="Test uses features that are currently only supported for AMD64. Skipping in CI."
    )
    only_on_arm64 = pytest.mark.skip(
        reason="Test uses features that are currently only supported for ARM64. Skipping in CI."
    )

    for item in items:
        if is_offline and "skip_offline" in item.keywords:
            item.add_marker(skip_offline)
        if not is_in_docker and "requires_in_container" in item.keywords:
            item.add_marker(requires_in_container)
        if is_in_ci and not is_amd64 and "only_on_amd64" in item.keywords:
            item.add_marker(only_on_amd64)
        if is_in_ci and not is_arm64 and "only_on_arm64" in item.keywords:
            item.add_marker(only_on_arm64)