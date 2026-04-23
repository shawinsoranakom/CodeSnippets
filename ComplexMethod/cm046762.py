def get_base_model_from_lora(lora_path: str) -> Optional[str]:
    """
    Read the base model name from a LoRA adapter's config.

    Args:
        lora_path: Path to the LoRA adapter directory

    Returns:
        Base model identifier or None if not found
    """
    try:
        lora_path_obj = Path(lora_path)

        if not _looks_like_lora_adapter(lora_path_obj):
            return None

        # Try adapter_config.json first
        adapter_config_path = lora_path_obj / "adapter_config.json"
        if adapter_config_path.exists():
            with open(adapter_config_path, "r") as f:
                config = json.load(f)
                base_model = config.get("base_model_name_or_path")
                if base_model:
                    logger.info(
                        f"Detected base model from adapter_config.json: {base_model}"
                    )
                    return base_model

        # Fallback: try training_args.bin (requires torch)
        training_args_path = lora_path_obj / "training_args.bin"
        if training_args_path.exists():
            try:
                import torch

                training_args = torch.load(training_args_path)
                if hasattr(training_args, "model_name_or_path"):
                    base_model = training_args.model_name_or_path
                    logger.info(
                        f"Detected base model from training_args.bin: {base_model}"
                    )
                    return base_model
            except Exception as e:
                logger.warning(f"Could not load training_args.bin: {e}")

        # Last resort: parse from directory name
        # Format: unsloth_Meta-Llama-3.1-8B-Instruct-bnb-4bit_timestamp
        dir_name = lora_path_obj.name
        if dir_name.startswith("unsloth_"):
            # Remove timestamp suffix (usually _1234567890)
            parts = dir_name.split("_")
            # Reconstruct model name
            if len(parts) >= 2:
                model_parts = parts[1:-1]  # Skip "unsloth" and timestamp
                base_model = "unsloth/" + "_".join(model_parts)
                logger.info(f"Detected base model from directory name: {base_model}")
                return base_model

        logger.warning(f"Could not detect base model for LoRA: {lora_path}")
        return None

    except Exception as e:
        logger.error(f"Error reading base model from LoRA config: {e}")
        return None