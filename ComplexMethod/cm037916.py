def _load_dense_weights(
    linear: nn.Linear, folder: str, model_config: "ModelConfig"
) -> bool:
    """Load weights using vLLM's weight_loader pattern."""
    from vllm.model_executor.model_loader.weight_utils import default_weight_loader

    for filename in ["model.safetensors", "pytorch_model.bin"]:
        file_path = f"{folder}/{filename}" if folder else filename

        try:
            file_bytes = get_hf_file_bytes(
                file_path, model_config.model, model_config.revision
            )
            if not file_bytes:
                continue

            if filename.endswith(".safetensors"):
                from safetensors.torch import load as load_safetensors

                state_dict = load_safetensors(file_bytes)
            else:
                import io

                state_dict = torch.load(
                    io.BytesIO(file_bytes), map_location="cpu", weights_only=True
                )

            for weight_key in ["weight", "linear.weight", "dense.weight"]:
                if weight_key in state_dict:
                    weight_loader = getattr(
                        linear.weight, "weight_loader", default_weight_loader
                    )
                    weight_loader(linear.weight, state_dict[weight_key])

                    bias_key = weight_key.replace("weight", "bias")
                    if linear.bias is not None and bias_key in state_dict:
                        bias_loader = getattr(
                            linear.bias, "weight_loader", default_weight_loader
                        )
                        bias_loader(linear.bias, state_dict[bias_key])
                    return True
        except Exception:
            logger.exception("Failed to load %s", filename)
            continue

    return False