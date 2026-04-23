def get_model_type_cases(
    model_type: str,
    test_info: VLMTestInfo,
    test_type: VLMTestType,
):
    # Ensure that something is wrapped as an iterable it's not already
    ensure_wrapped = lambda e: e if isinstance(e, (list, tuple)) else (e,)

    # This is essentially the same as nesting a bunch of mark.parametrize
    # decorators, but we do it programmatically to allow overrides for on
    # a per-model basis, while still being able to execute each of these
    # as individual test cases in pytest.
    iter_kwargs = OrderedDict(
        [
            ("model", ensure_wrapped(test_info.models)),
            ("max_tokens", ensure_wrapped(test_info.max_tokens)),
            ("num_logprobs", ensure_wrapped(test_info.num_logprobs)),
            ("dtype", ensure_wrapped(test_info.dtype)),
            (
                "distributed_executor_backend",
                ensure_wrapped(test_info.distributed_executor_backend),
            ),
        ]
    )

    # num_frames is video only
    if test_type == VLMTestType.VIDEO:
        iter_kwargs["num_video_frames"] = ensure_wrapped(test_info.num_video_frames)
        iter_kwargs["needs_video_metadata"] = ensure_wrapped(
            test_info.needs_video_metadata
        )

    # No sizes passed for custom inputs, since inputs are directly provided
    if test_type not in (
        VLMTestType.CUSTOM_INPUTS,
        VLMTestType.AUDIO,
    ):
        wrapped_sizes = get_wrapped_test_sizes(test_info, test_type)
        if wrapped_sizes is None:
            raise ValueError(f"Sizes must be set for test type {test_type}")
        iter_kwargs["size_wrapper"] = wrapped_sizes

    # Otherwise expand the custom test options instead
    elif test_type == VLMTestType.CUSTOM_INPUTS:
        if test_info.custom_test_opts is None:
            raise ValueError("Test has type CUSTOM_INPUTS, but none given")
        iter_kwargs["custom_test_opts"] = test_info.custom_test_opts

    # Wrap all model cases in a pytest parameter & pass marks through
    return [
        pytest.param(
            model_type,
            ExpandableVLMTestArgs(**{k: v for k, v in zip(iter_kwargs.keys(), case)}),
            marks=test_info.marks if test_info.marks is not None else [],
        )
        for case in list(itertools.product(*iter_kwargs.values()))
    ]