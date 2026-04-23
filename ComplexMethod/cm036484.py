def get_vllm_extra_kwargs(model_info: ModelInfo, vllm_extra_kwargs):
    # A model family has many models with the same architecture,
    # and we don't need to test each one.
    if not ci_envs.VLLM_CI_NO_SKIP and not model_info.enable_test:
        import pytest

        pytest.skip("Skipping test.")

    # Allow vllm to test using the given dtype, such as float32
    vllm_extra_kwargs = vllm_extra_kwargs or {}
    vllm_extra_kwargs["dtype"] = ci_envs.VLLM_CI_DTYPE or model_info.dtype

    # Allow vllm to test using hf_overrides
    if model_info.hf_overrides is not None:
        vllm_extra_kwargs["hf_overrides"] = model_info.hf_overrides

    # Allow changing the head dtype used by vllm in tests
    if ci_envs.VLLM_CI_HEAD_DTYPE is not None:
        if "hf_overrides" not in vllm_extra_kwargs:
            vllm_extra_kwargs["hf_overrides"] = {}
        vllm_extra_kwargs["hf_overrides"]["head_dtype"] = ci_envs.VLLM_CI_HEAD_DTYPE

    # Allow control over whether tests use enforce_eager
    if ci_envs.VLLM_CI_ENFORCE_EAGER is not None:
        vllm_extra_kwargs["enforce_eager"] = ci_envs.VLLM_CI_ENFORCE_EAGER

    return vllm_extra_kwargs