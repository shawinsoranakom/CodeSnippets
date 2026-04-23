def execute(cls, model_name) -> io.NodeOutput:
        model_path = folder_paths.get_full_path_or_raise("latent_upscale_models", model_name)
        sd, metadata = comfy.utils.load_torch_file(model_path, safe_load=True, return_metadata=True)

        if "blocks.0.block.0.conv.weight" in sd:
            config = {
                "in_channels": sd["in_conv.conv.weight"].shape[1],
                "out_channels": sd["out_conv.conv.weight"].shape[0],
                "hidden_channels": sd["in_conv.conv.weight"].shape[0],
                "num_blocks": len([k for k in sd.keys() if k.startswith("blocks.") and k.endswith(".block.0.conv.weight")]),
                "global_residual": False,
            }
            model_type = "720p"
            model = HunyuanVideo15SRModel(model_type, config)
            model.load_sd(sd)
        elif "up.0.block.0.conv1.conv.weight" in sd:
            sd = {key.replace("nin_shortcut", "nin_shortcut.conv", 1): value for key, value in sd.items()}
            config = {
                "z_channels": sd["conv_in.conv.weight"].shape[1],
                "out_channels": sd["conv_out.conv.weight"].shape[0],
                "block_out_channels": tuple(sd[f"up.{i}.block.0.conv1.conv.weight"].shape[0] for i in range(len([k for k in sd.keys() if k.startswith("up.") and k.endswith(".block.0.conv1.conv.weight")]))),
            }
            model_type = "1080p"
            model = HunyuanVideo15SRModel(model_type, config)
            model.load_sd(sd)
        elif "post_upsample_res_blocks.0.conv2.bias" in sd:
            config = json.loads(metadata["config"])
            model = LatentUpsampler.from_config(config).to(dtype=comfy.model_management.vae_dtype(allowed_dtypes=[torch.bfloat16, torch.float32]))
            model.load_state_dict(sd)

        return io.NodeOutput(model)