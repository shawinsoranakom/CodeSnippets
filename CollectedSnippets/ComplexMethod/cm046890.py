def fix_vllm_guided_decoding_params():
    def _maybe_raise_vllm_transformers_mismatch(error):
        error_text = str(error)
        if (
            "ALLOWED_LAYER_TYPES" in error_text
            or "transformers.configuration_utils" in error_text
        ):
            try:
                vllm_version = importlib_version("vllm")
            except Exception:
                vllm_version = "unknown"
            raise RuntimeError(
                "Unsloth: vLLM with version "
                f"{vllm_version} does not yet support transformers>=5.0.0. "
                "Please downgrade to transformers==4.57.3 via "
                'pip install --force-reinstall "transformers==4.57.3". '
                f"Original error: {error}"
            ) from error

    if importlib.util.find_spec("vllm") is None:
        return
    # GuidedDecodingParmas is renamed to StructuredOutputsParams in vLLM
    # https://github.com/vllm-project/vllm/pull/22772/files
    # trl still wants to use GuidedDecodingParams. This is a temporary patch till trl updates
    try:
        import vllm
    except (ImportError, OSError) as e:
        _maybe_raise_vllm_transformers_mismatch(e)
        if disable_broken_vllm(e):
            return
        raise

    try:
        from vllm.sampling_params import GuidedDecodingParams
    except (ImportError, OSError) as e:
        _maybe_raise_vllm_transformers_mismatch(e)
        if disable_broken_vllm(e):
            return
        if not hasattr(vllm, "sampling_params") or not hasattr(
            vllm.sampling_params, "StructuredOutputsParams"
        ):
            raise
        vllm.sampling_params.GuidedDecodingParams = (
            vllm.sampling_params.StructuredOutputsParams
        )