def load_model_patch(self, name):
        model_patch_path = folder_paths.get_full_path_or_raise("model_patches", name)
        sd = comfy.utils.load_torch_file(model_patch_path, safe_load=True)
        dtype = comfy.utils.weight_dtype(sd)

        if 'controlnet_blocks.0.y_rms.weight' in sd:
            additional_in_dim = sd["img_in.weight"].shape[1] - 64
            model = QwenImageBlockWiseControlNet(additional_in_dim=additional_in_dim, device=comfy.model_management.unet_offload_device(), dtype=dtype, operations=comfy.ops.manual_cast)
        elif 'feature_embedder.mid_layer_norm.bias' in sd:
            sd = comfy.utils.state_dict_prefix_replace(sd, {"feature_embedder.": ""}, filter_keys=True)
            model = SigLIPMultiFeatProjModel(device=comfy.model_management.unet_offload_device(), dtype=dtype, operations=comfy.ops.manual_cast)
        elif 'control_all_x_embedder.2-1.weight' in sd: # alipai z image fun controlnet
            sd = z_image_convert(sd)
            config = {}
            if 'control_layers.4.adaLN_modulation.0.weight' not in sd:
                config['n_control_layers'] = 3
                config['additional_in_dim'] = 17
                config['refiner_control'] = True
            if 'control_layers.14.adaLN_modulation.0.weight' in sd:
                config['n_control_layers'] = 15
                config['additional_in_dim'] = 17
                config['refiner_control'] = True
                ref_weight = sd.get("control_noise_refiner.0.after_proj.weight", None)
                if ref_weight is not None:
                    if torch.count_nonzero(ref_weight) == 0:
                        config['broken'] = True
            model = comfy.ldm.lumina.controlnet.ZImage_Control(device=comfy.model_management.unet_offload_device(), dtype=dtype, operations=comfy.ops.manual_cast, **config)
        elif "audio_proj.proj1.weight" in sd:
            model = MultiTalkModelPatch(
                    audio_window=5, context_tokens=32, vae_scale=4,
                    in_dim=sd["blocks.0.audio_cross_attn.proj.weight"].shape[0],
                    intermediate_dim=sd["audio_proj.proj1.weight"].shape[0],
                    out_dim=sd["audio_proj.norm.weight"].shape[0],
                    device=comfy.model_management.unet_offload_device(),
                    operations=comfy.ops.manual_cast)
        elif 'model.control_model.input_hint_block.0.weight' in sd or 'control_model.input_hint_block.0.weight' in sd:
            prefix_replace = {}
            if 'model.control_model.input_hint_block.0.weight' in sd:
                prefix_replace["model.control_model."] = "control_model."
                prefix_replace["model.diffusion_model.project_modules."] = "project_modules."
            else:
                prefix_replace["control_model."] = "control_model."
                prefix_replace["project_modules."] = "project_modules."

            # Extract denoise_encoder weights before filter_keys discards them
            de_prefix = "first_stage_model.denoise_encoder."
            denoise_encoder_sd = {}
            for k in list(sd.keys()):
                if k.startswith(de_prefix):
                    denoise_encoder_sd[k[len(de_prefix):]] = sd.pop(k)

            sd = comfy.utils.state_dict_prefix_replace(sd, prefix_replace, filter_keys=True)
            sd.pop("control_model.mask_LQ", None)
            model = comfy.ldm.supir.supir_modules.SUPIR(device=comfy.model_management.unet_offload_device(), dtype=dtype, operations=comfy.ops.manual_cast)
            if denoise_encoder_sd:
                model.denoise_encoder_sd = denoise_encoder_sd

        model_patcher = comfy.model_patcher.CoreModelPatcher(model, load_device=comfy.model_management.get_torch_device(), offload_device=comfy.model_management.unet_offload_device())
        model.load_state_dict(sd, assign=model_patcher.is_dynamic())
        return (model_patcher,)