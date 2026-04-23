def _get_model_size_bytes(
    model_name: str, hf_token: Optional[str] = None
) -> Optional[int]:
    """Get total size of model weight files from HF Hub."""
    try:
        from huggingface_hub import HfApi

        api = HfApi(token = hf_token)
        info = api.repo_info(model_name, repo_type = "model", token = hf_token)
        if not info.siblings:
            return None

        weight_exts = (".safetensors", ".bin", ".pt", ".pth", ".gguf")
        total = 0
        for sibling in info.siblings:
            if sibling.rfilename and any(
                sibling.rfilename.endswith(ext) for ext in weight_exts
            ):
                if sibling.size is not None:
                    total += sibling.size

        return total if total > 0 else None
    except Exception as e:
        logger.warning(f"Could not get model size for {model_name}: {e}")
        return None