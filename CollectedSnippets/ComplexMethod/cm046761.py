def get_base_model_from_checkpoint(checkpoint_path: str) -> Optional[str]:
    """Read the base model name from a local training or checkpoint directory."""
    try:
        checkpoint_path_obj = Path(checkpoint_path)

        adapter_config_path = checkpoint_path_obj / "adapter_config.json"
        if adapter_config_path.exists():
            with open(adapter_config_path, "r") as f:
                config = json.load(f)
                base_model = config.get("base_model_name_or_path")
                if base_model:
                    logger.info(
                        "Detected base model from adapter_config.json: %s", base_model
                    )
                    return base_model

        config_path = checkpoint_path_obj / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                for key in ("model_name", "_name_or_path"):
                    base_model = config.get(key)
                    if base_model and str(base_model) != str(checkpoint_path_obj):
                        logger.info(
                            "Detected base model from config.json (%s): %s",
                            key,
                            base_model,
                        )
                        return base_model

        training_args_path = checkpoint_path_obj / "training_args.bin"
        if training_args_path.exists():
            try:
                import torch

                training_args = torch.load(training_args_path)
                if hasattr(training_args, "model_name_or_path"):
                    base_model = training_args.model_name_or_path
                    logger.info(
                        "Detected base model from training_args.bin: %s", base_model
                    )
                    return base_model
            except Exception as e:
                logger.warning(f"Could not load training_args.bin: {e}")

        dir_name = checkpoint_path_obj.name
        if dir_name.startswith("unsloth_"):
            parts = dir_name.split("_")
            if len(parts) >= 2:
                model_parts = parts[1:-1]
                base_model = "unsloth/" + "_".join(model_parts)
                logger.info("Detected base model from directory name: %s", base_model)
                return base_model

        logger.warning(f"Could not detect base model for checkpoint: {checkpoint_path}")
        return None

    except Exception as e:
        logger.error(f"Error reading base model from checkpoint config: {e}")
        return None