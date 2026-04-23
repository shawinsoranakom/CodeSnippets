def _should_skip_xfail_test_sample(
    op_name: str, sample, dtype: torch.dtype, device_type: str
) -> tuple[str | None, str | None]:
    """Returns a reason if a test sample should be skipped."""
    if op_name not in ops_test_data.OP_WITH_SKIPPED_XFAIL_SUBTESTS:
        return None, None
    for decorator_meta in ops_test_data.SKIP_XFAIL_SUBTESTS:
        # Linear search on ops_test_data.SKIP_XFAIL_SUBTESTS. That's fine because the list is small.
        if decorator_meta.op_name == op_name:
            if decorator_meta.matcher is None:
                raise AssertionError("Matcher must be defined")
            if not decorator_meta.enabled_if:
                # Do not skip the test if the decorator meta is not enabled
                continue
            if decorator_meta.dtypes is not None and dtype not in decorator_meta.dtypes:
                # Not applicable for this dtype
                continue
            if (
                decorator_meta.device_type is not None
                and decorator_meta.device_type != device_type
            ):
                # Not applicable for this device_type
                continue
            if decorator_meta.matcher(sample):
                return decorator_meta.test_behavior, decorator_meta.reason
    return None, None