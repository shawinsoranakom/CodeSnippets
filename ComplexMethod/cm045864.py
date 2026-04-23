def from_checkpoint(cls, model_path: str, model_filename: str = "pytorch_model.pth", state_dict_strip_prefix="model.model."):
        config = VisionEncoderDecoderConfig.from_pretrained(model_path)
        config._name_or_path = model_path
        config.encoder = UnimerSwinConfig(**vars(config.encoder))
        config.decoder = UnimerMBartConfig(**vars(config.decoder))

        encoder = UnimerSwinModel(config.encoder)
        decoder = UnimerMBartForCausalLM(config.decoder)
        model = cls(config, encoder, decoder)

        # load model weights
        model_file_path = os.path.join(model_path, model_filename)
        checkpoint = torch.load(model_file_path, map_location="cpu", weights_only=True)
        state_dict = checkpoint["model"] if "model" in checkpoint else checkpoint
        if not state_dict:
            raise RuntimeError("state_dict is empty.")
        if state_dict_strip_prefix:
            state_dict = {
                k[len(state_dict_strip_prefix):] if k.startswith(state_dict_strip_prefix) else k: v
                for k, v in state_dict.items()
            }
        missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
        if len(unexpected_keys) > 0:
            warnings.warn("Unexpected key(s) in state_dict: {}.".format(", ".join(f'"{k}"' for k in unexpected_keys)))
        if len(missing_keys) > 0:
            raise RuntimeError("Missing key(s) in state_dict: {}.".format(", ".join(f'"{k}"' for k in missing_keys)))
        return model