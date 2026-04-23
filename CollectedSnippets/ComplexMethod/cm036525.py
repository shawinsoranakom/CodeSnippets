def _assert_inputs_equal(
    a: MultiModalInput,
    b: MultiModalInput,
    *,
    ignore_mm_keys: set[str] | None = None,
    msg: str = "",
):
    if ignore_mm_keys is None:
        ignore_mm_keys = set()

    ignore_prompt_keys = ("prompt", "mm_kwargs")
    a_rest = {k: v for k, v in a.items() if k not in ignore_prompt_keys}
    b_rest = {k: v for k, v in b.items() if k not in ignore_prompt_keys}

    assert a_rest == b_rest, msg

    a_data = a["mm_kwargs"].get_data()
    b_data = b["mm_kwargs"].get_data()

    for key in ignore_mm_keys:
        a_data.pop(key, None)
        b_data.pop(key, None)

    assert batched_tensors_equal(a_data, b_data), msg