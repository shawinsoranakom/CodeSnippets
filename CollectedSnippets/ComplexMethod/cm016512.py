def model_lora_keys_unet(model, key_map={}):
    sd = model.state_dict()
    sdk = sd.keys()

    for k in sdk:
        if k.startswith("diffusion_model."):
            if k.endswith(".weight"):
                key_lora = k[len("diffusion_model."):-len(".weight")].replace(".", "_")
                key_map["lora_unet_{}".format(key_lora)] = k
                key_map["{}".format(k[:-len(".weight")])] = k #generic lora format without any weird key names
            else:
                key_map["{}".format(k)] = k #generic lora format for not .weight without any weird key names

    diffusers_keys = comfy.utils.unet_to_diffusers(model.model_config.unet_config)
    for k in diffusers_keys:
        if k.endswith(".weight"):
            unet_key = "diffusion_model.{}".format(diffusers_keys[k])
            key_lora = k[:-len(".weight")].replace(".", "_")
            key_map["lora_unet_{}".format(key_lora)] = unet_key
            key_map["lycoris_{}".format(key_lora)] = unet_key #simpletuner lycoris format

            diffusers_lora_prefix = ["", "unet."]
            for p in diffusers_lora_prefix:
                diffusers_lora_key = "{}{}".format(p, k[:-len(".weight")].replace(".to_", ".processor.to_"))
                if diffusers_lora_key.endswith(".to_out.0"):
                    diffusers_lora_key = diffusers_lora_key[:-2]
                key_map[diffusers_lora_key] = unet_key

    if isinstance(model, comfy.model_base.StableCascade_C):
        for k in sdk:
            if k.startswith("diffusion_model."):
                if k.endswith(".weight"):
                    key_lora = k[len("diffusion_model."):-len(".weight")].replace(".", "_")
                    key_map["lora_prior_unet_{}".format(key_lora)] = k

    if isinstance(model, comfy.model_base.SD3): #Diffusers lora SD3
        diffusers_keys = comfy.utils.mmdit_to_diffusers(model.model_config.unet_config, output_prefix="diffusion_model.")
        for k in diffusers_keys:
            if k.endswith(".weight"):
                to = diffusers_keys[k]
                key_lora = "transformer.{}".format(k[:-len(".weight")]) #regular diffusers sd3 lora format
                key_map[key_lora] = to

                key_lora = "base_model.model.{}".format(k[:-len(".weight")]) #format for flash-sd3 lora and others?
                key_map[key_lora] = to

                key_lora = "lora_transformer_{}".format(k[:-len(".weight")].replace(".", "_")) #OneTrainer lora
                key_map[key_lora] = to

                key_lora = "lycoris_{}".format(k[:-len(".weight")].replace(".", "_")) #simpletuner lycoris format
                key_map[key_lora] = to

    if isinstance(model, comfy.model_base.AuraFlow): #Diffusers lora AuraFlow
        diffusers_keys = comfy.utils.auraflow_to_diffusers(model.model_config.unet_config, output_prefix="diffusion_model.")
        for k in diffusers_keys:
            if k.endswith(".weight"):
                to = diffusers_keys[k]
                key_lora = "transformer.{}".format(k[:-len(".weight")]) #simpletrainer and probably regular diffusers lora format
                key_map[key_lora] = to

    if isinstance(model, comfy.model_base.PixArt):
        diffusers_keys = comfy.utils.pixart_to_diffusers(model.model_config.unet_config, output_prefix="diffusion_model.")
        for k in diffusers_keys:
            if k.endswith(".weight"):
                to = diffusers_keys[k]
                key_lora = "transformer.{}".format(k[:-len(".weight")]) #default format
                key_map[key_lora] = to

                key_lora = "base_model.model.{}".format(k[:-len(".weight")]) #diffusers training script
                key_map[key_lora] = to

                key_lora = "unet.base_model.model.{}".format(k[:-len(".weight")]) #old reference peft script
                key_map[key_lora] = to

    if isinstance(model, comfy.model_base.HunyuanDiT):
        for k in sdk:
            if k.startswith("diffusion_model.") and k.endswith(".weight"):
                key_lora = k[len("diffusion_model."):-len(".weight")]
                key_map["base_model.model.{}".format(key_lora)] = k #official hunyuan lora format

    if isinstance(model, comfy.model_base.Flux): #Diffusers lora Flux
        diffusers_keys = comfy.utils.flux_to_diffusers(model.model_config.unet_config, output_prefix="diffusion_model.")
        for k in diffusers_keys:
            if k.endswith(".weight"):
                to = diffusers_keys[k]
                key_map["transformer.{}".format(k[:-len(".weight")])] = to #simpletrainer and probably regular diffusers flux lora format
                key_map["lycoris_{}".format(k[:-len(".weight")].replace(".", "_"))] = to #simpletrainer lycoris
                key_map["lora_transformer_{}".format(k[:-len(".weight")].replace(".", "_"))] = to #onetrainer
                key_map[k[:-len(".weight")]] = to #DiffSynth lora format
        for k in sdk:
            hidden_size = model.model_config.unet_config.get("hidden_size", 0)
            if k.endswith(".weight") and ".linear1." in k:
                key_map["{}".format(k.replace(".linear1.weight", ".linear1_qkv"))] = (k, (0, 0, hidden_size * 3))

    if isinstance(model, comfy.model_base.GenmoMochi):
        for k in sdk:
            if k.startswith("diffusion_model.") and k.endswith(".weight"): #Official Mochi lora format
                key_lora = k[len("diffusion_model."):-len(".weight")]
                key_map["{}".format(key_lora)] = k

    if isinstance(model, comfy.model_base.HunyuanVideo):
        for k in sdk:
            if k.startswith("diffusion_model.") and k.endswith(".weight"):
                # diffusion-pipe lora format
                key_lora = k
                key_lora = key_lora.replace("_mod.lin.", "_mod.linear.").replace("_attn.qkv.", "_attn_qkv.").replace("_attn.proj.", "_attn_proj.")
                key_lora = key_lora.replace("mlp.0.", "mlp.fc1.").replace("mlp.2.", "mlp.fc2.")
                key_lora = key_lora.replace(".modulation.lin.", ".modulation.linear.")
                key_lora = key_lora[len("diffusion_model."):-len(".weight")]
                key_map["transformer.{}".format(key_lora)] = k
                key_map["diffusion_model.{}".format(key_lora)] = k  # Old loras

    if isinstance(model, comfy.model_base.HiDream):
        for k in sdk:
            if k.startswith("diffusion_model."):
                if k.endswith(".weight"):
                    key_lora = k[len("diffusion_model."):-len(".weight")]
                    key_map["lycoris_{}".format(key_lora.replace(".", "_"))] = k #SimpleTuner lycoris format
                    key_map["transformer.{}".format(key_lora)] = k #SimpleTuner regular format

    if isinstance(model, comfy.model_base.ACEStep):
        for k in sdk:
            if k.startswith("diffusion_model.") and k.endswith(".weight"): #Official ACE step lora format
                key_lora = k[len("diffusion_model."):-len(".weight")]
                key_map["{}".format(key_lora)] = k

    if isinstance(model, comfy.model_base.Omnigen2):
        for k in sdk:
            if k.startswith("diffusion_model.") and k.endswith(".weight"):
                key_lora = k[len("diffusion_model."):-len(".weight")]
                key_map["{}".format(key_lora)] = k

    if isinstance(model, comfy.model_base.QwenImage):
        for k in sdk:
            if k.startswith("diffusion_model.") and k.endswith(".weight"): #QwenImage lora format
                key_lora = k[len("diffusion_model."):-len(".weight")]
                # Direct mapping for transformer_blocks format (QwenImage LoRA format)
                key_map["{}".format(key_lora)] = k
                # Support transformer prefix format
                key_map["transformer.{}".format(key_lora)] = k
                key_map["lycoris_{}".format(key_lora.replace(".", "_"))] = k #SimpleTuner lycoris format

    if isinstance(model, comfy.model_base.Lumina2):
        diffusers_keys = comfy.utils.z_image_to_diffusers(model.model_config.unet_config, output_prefix="diffusion_model.")
        for k in diffusers_keys:
            if k.endswith(".weight"):
                to = diffusers_keys[k]
                key_lora = k[:-len(".weight")]
                key_map["diffusion_model.{}".format(key_lora)] = to
                key_map["transformer.{}".format(key_lora)] = to
                key_map["lycoris_{}".format(key_lora.replace(".", "_"))] = to
                key_map[key_lora] = to

    if isinstance(model, comfy.model_base.Kandinsky5):
        for k in sdk:
            if k.startswith("diffusion_model.") and k.endswith(".weight"):
                key_lora = k[len("diffusion_model."):-len(".weight")]
                key_map["{}".format(key_lora)] = k
                key_map["transformer.{}".format(key_lora)] = k

    if isinstance(model, comfy.model_base.ACEStep15):
        for k in sdk:
            if k.startswith("diffusion_model.decoder.") and k.endswith(".weight"):
                key_lora = k[len("diffusion_model.decoder."):-len(".weight")]
                key_map["base_model.model.{}".format(key_lora)] = k  # Official base model loras
                key_map["lycoris_{}".format(key_lora.replace(".", "_"))] = k  # LyCORIS/LoKR format

    return key_map