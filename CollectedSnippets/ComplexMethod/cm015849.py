def _run_and_assert_no_indirect_indexing(
    test_case, func, *args, has_wrapping=None, has_assert=False, **kwargs
):
    result, source_codes = run_and_get_code(func, *args, **kwargs)

    for code in source_codes:
        for line in code.split("\n"):
            stmt = None
            # Find indexing expressions
            if ".load(" in line:
                stmt = line.split(".load")[-1]
            elif "tl.store" in line:
                stmt = line.split(".store")[-1]
                stmt = ",".join(stmt.split(",")[:-2])  # Remove store value and mask
            elif ".store" in line:
                stmt = line.split(".store")[-1]
            elif "[" in line:
                stmt = line.split("[")[-1].split("]")[0]
            # Block descriptors do not support indirect indexing
            if any(
                block_descriptor_syntax in line
                for block_descriptor_syntax in (
                    "block_ptr",
                    "tma_descriptor",
                    "tl.make_block_ptr",
                    "tl.make_tensor_descriptor",
                )
            ):
                continue

            if stmt is None:
                continue

            # indirect indexing involves a `tmp` variable
            test_case.assertTrue(
                "tmp" not in stmt,
                msg=f"Found indirect indexing in statement '{stmt}' from code:\n{code}",
            )
        if has_wrapping is not None:
            test_case.assertTrue(
                ("where" in code or ") ? (" in code) is has_wrapping,
                msg=f"Wanted {has_wrapping=} but got\n{code}",
            )

    def has_assert_in_code(code):
        # Check for device_assert, or TORCH_CHECK that isn't AOTI_TORCH_CHECK
        # AOTI_TORCH_CHECK is for lazy Triton compile infrastructure, not bounds checking
        if "device_assert" in code:
            return True
        for line in code.split("\n"):
            if "TORCH_CHECK" in line and "AOTI_TORCH_CHECK" not in line:
                return True
        return False

    test_case.assertTrue(
        any(has_assert_in_code(code) is has_assert for code in source_codes)
    )
    return result