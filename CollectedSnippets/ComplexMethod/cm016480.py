def load_controlnet_state_dict(state_dict, model=None, model_options={}):
    controlnet_data = state_dict
    if 'after_proj_list.18.bias' in controlnet_data.keys(): #Hunyuan DiT
        return load_controlnet_hunyuandit(controlnet_data, model_options=model_options)

    if "lora_controlnet" in controlnet_data:
        return ControlLora(controlnet_data, model_options=model_options)

    controlnet_config = None
    supported_inference_dtypes = None

    if "controlnet_cond_embedding.conv_in.weight" in controlnet_data: #diffusers format
        controlnet_config = comfy.model_detection.unet_config_from_diffusers_unet(controlnet_data)
        diffusers_keys = comfy.utils.unet_to_diffusers(controlnet_config)
        diffusers_keys["controlnet_mid_block.weight"] = "middle_block_out.0.weight"
        diffusers_keys["controlnet_mid_block.bias"] = "middle_block_out.0.bias"

        count = 0
        loop = True
        while loop:
            suffix = [".weight", ".bias"]
            for s in suffix:
                k_in = "controlnet_down_blocks.{}{}".format(count, s)
                k_out = "zero_convs.{}.0{}".format(count, s)
                if k_in not in controlnet_data:
                    loop = False
                    break
                diffusers_keys[k_in] = k_out
            count += 1

        count = 0
        loop = True
        while loop:
            suffix = [".weight", ".bias"]
            for s in suffix:
                if count == 0:
                    k_in = "controlnet_cond_embedding.conv_in{}".format(s)
                else:
                    k_in = "controlnet_cond_embedding.blocks.{}{}".format(count - 1, s)
                k_out = "input_hint_block.{}{}".format(count * 2, s)
                if k_in not in controlnet_data:
                    k_in = "controlnet_cond_embedding.conv_out{}".format(s)
                    loop = False
                diffusers_keys[k_in] = k_out
            count += 1

        new_sd = {}
        for k in diffusers_keys:
            if k in controlnet_data:
                new_sd[diffusers_keys[k]] = controlnet_data.pop(k)

        if "control_add_embedding.linear_1.bias" in controlnet_data: #Union Controlnet
            controlnet_config["union_controlnet_num_control_type"] = controlnet_data["task_embedding"].shape[0]
            for k in list(controlnet_data.keys()):
                new_k = k.replace('.attn.in_proj_', '.attn.in_proj.')
                new_sd[new_k] = controlnet_data.pop(k)

        leftover_keys = controlnet_data.keys()
        if len(leftover_keys) > 0:
            logging.warning("leftover keys: {}".format(leftover_keys))
        controlnet_data = new_sd
    elif "controlnet_blocks.0.weight" in controlnet_data:
        if "double_blocks.0.img_attn.norm.key_norm.scale" in controlnet_data:
            return load_controlnet_flux_xlabs_mistoline(controlnet_data, model_options=model_options)
        elif "pos_embed_input.proj.weight" in controlnet_data:
            if "transformer_blocks.0.adaLN_modulation.1.bias" in controlnet_data:
                return load_controlnet_sd35(controlnet_data, model_options=model_options) #Stability sd3.5 format
            else:
                return load_controlnet_mmdit(controlnet_data, model_options=model_options) #SD3 diffusers controlnet
        elif "transformer_blocks.0.img_mlp.net.0.proj.weight" in controlnet_data:
            return load_controlnet_qwen_instantx(controlnet_data, model_options=model_options)
        elif "controlnet_x_embedder.weight" in controlnet_data:
            return load_controlnet_flux_instantx(controlnet_data, model_options=model_options)
    elif "control_blocks.0.after_proj.weight" in controlnet_data and "control_img_in.weight" in controlnet_data:
        return load_controlnet_qwen_fun(controlnet_data, model_options=model_options)

    elif "controlnet_blocks.0.linear.weight" in controlnet_data: #mistoline flux
        return load_controlnet_flux_xlabs_mistoline(convert_mistoline(controlnet_data), mistoline=True, model_options=model_options)

    pth_key = 'control_model.zero_convs.0.0.weight'
    pth = False
    key = 'zero_convs.0.0.weight'
    if pth_key in controlnet_data:
        pth = True
        key = pth_key
        prefix = "control_model."
    elif key in controlnet_data:
        prefix = ""
    else:
        net = load_t2i_adapter(controlnet_data, model_options=model_options)
        if net is None:
            logging.error("error could not detect control model type.")
        return net

    if controlnet_config is None:
        model_config = comfy.model_detection.model_config_from_unet(controlnet_data, prefix, True)
        supported_inference_dtypes = list(model_config.supported_inference_dtypes)
        controlnet_config = model_config.unet_config

    unet_dtype = model_options.get("dtype", None)
    if unet_dtype is None:
        weight_dtype = comfy.utils.weight_dtype(controlnet_data)

        if supported_inference_dtypes is None:
            supported_inference_dtypes = [comfy.model_management.unet_dtype()]

        unet_dtype = comfy.model_management.unet_dtype(model_params=-1, supported_dtypes=supported_inference_dtypes, weight_dtype=weight_dtype)

    load_device = comfy.model_management.get_torch_device()

    manual_cast_dtype = comfy.model_management.unet_manual_cast(unet_dtype, load_device)
    operations = model_options.get("custom_operations", None)
    if operations is None:
        operations = comfy.ops.pick_operations(unet_dtype, manual_cast_dtype)

    controlnet_config["operations"] = operations
    controlnet_config["dtype"] = unet_dtype
    controlnet_config["device"] = comfy.model_management.unet_offload_device()
    controlnet_config.pop("out_channels")
    controlnet_config["hint_channels"] = controlnet_data["{}input_hint_block.0.weight".format(prefix)].shape[1]
    control_model = comfy.cldm.cldm.ControlNet(**controlnet_config)

    if pth:
        if 'difference' in controlnet_data:
            if model is not None:
                comfy.model_management.load_models_gpu([model])
                model_sd = model.model_state_dict()
                for x in controlnet_data:
                    c_m = "control_model."
                    if x.startswith(c_m):
                        sd_key = "diffusion_model.{}".format(x[len(c_m):])
                        if sd_key in model_sd:
                            cd = controlnet_data[x]
                            cd += model_sd[sd_key].type(cd.dtype).to(cd.device)
            else:
                logging.warning("WARNING: Loaded a diff controlnet without a model. It will very likely not work.")

        class WeightsLoader(torch.nn.Module):
            pass
        w = WeightsLoader()
        w.control_model = control_model
        missing, unexpected = w.load_state_dict(controlnet_data, strict=False)
    else:
        missing, unexpected = control_model.load_state_dict(controlnet_data, strict=False)

    if len(missing) > 0:
        logging.warning("missing controlnet keys: {}".format(missing))

    if len(unexpected) > 0:
        logging.debug("unexpected controlnet keys: {}".format(unexpected))

    global_average_pooling = model_options.get("global_average_pooling", False)
    control = ControlNet(control_model, global_average_pooling=global_average_pooling, load_device=load_device, manual_cast_dtype=manual_cast_dtype)
    return control