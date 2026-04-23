def _is_vision_model_uncached(
    model_name: str, hf_token: Optional[str] = None
) -> Optional[bool]:
    """Uncached vision model detection -- called by is_vision_model().

    Returns True/False for definitive results, or None when detection failed
    due to a transient error (network, timeout, subprocess failure) so the
    caller knows not to cache the result.

    Do not call directly; use is_vision_model() instead.
    """
    # Models that need transformers 5.x must be checked in a subprocess
    # because AutoConfig in the main process (transformers 4.57.x) doesn't
    # recognize their architectures.
    from utils.transformers_version import needs_transformers_5

    if needs_transformers_5(model_name):
        logger.info(
            "Model '%s' needs transformers 5.x -- checking vision via subprocess",
            model_name,
        )
        return _is_vision_model_subprocess(model_name, hf_token = hf_token)

    try:
        config = load_model_config(model_name, use_auth = True, token = hf_token)

        # Exclude audio-only models that share ForConditionalGeneration suffix
        # (e.g. CsmForConditionalGeneration, WhisperForConditionalGeneration)
        _audio_only_model_types = {"csm", "whisper"}
        model_type = getattr(config, "model_type", None)
        if model_type in _audio_only_model_types:
            return False

        # Check 1: Architecture class name patterns
        if hasattr(config, "architectures"):
            is_vlm = any(x.endswith(_VLM_ARCH_SUFFIXES) for x in config.architectures)
            if is_vlm:
                logger.info(
                    f"Model {model_name} detected as VLM: architecture {config.architectures}"
                )
                return True

        # Check 2: Has vision_config (most VLMs: LLaVA, Gemma-3, Qwen2-VL, etc.)
        if hasattr(config, "vision_config"):
            logger.info(f"Model {model_name} detected as VLM: has vision_config")
            return True

        # Check 3: Has img_processor (Phi-3.5 Vision uses this instead of vision_config)
        if hasattr(config, "img_processor"):
            logger.info(f"Model {model_name} detected as VLM: has img_processor")
            return True

        # Check 4: Has image_token_index (common in VLMs for image placeholder tokens)
        if hasattr(config, "image_token_index"):
            logger.info(f"Model {model_name} detected as VLM: has image_token_index")
            return True

        # Check 5: Known VLM model_type values that may not match above checks
        if hasattr(config, "model_type"):
            if config.model_type in _VLM_MODEL_TYPES:
                logger.info(
                    f"Model {model_name} detected as VLM: model_type={config.model_type}"
                )
                return True

        return False

    except Exception as e:
        logger.warning(f"Could not determine if {model_name} is vision model: {e}")
        # Permanent failures (model not found, gated, bad config) should be
        # cached as False. Transient failures (network, timeout) should not.
        try:
            from huggingface_hub.errors import RepositoryNotFoundError, GatedRepoError
        except ImportError:
            try:
                from huggingface_hub.utils import (
                    RepositoryNotFoundError,
                    GatedRepoError,
                )
            except ImportError:
                RepositoryNotFoundError = GatedRepoError = None
        if RepositoryNotFoundError is not None and isinstance(
            e, (RepositoryNotFoundError, GatedRepoError)
        ):
            return False
        if isinstance(e, (ValueError, json.JSONDecodeError)):
            return False
        return None