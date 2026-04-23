def load_controlnet_sd35(sd, model_options={}):
    control_type = -1
    if "control_type" in sd:
        control_type = round(sd.pop("control_type").item())

    # blur_cnet = control_type == 0
    canny_cnet = control_type == 1
    depth_cnet = control_type == 2

    new_sd = {}
    for k in comfy.utils.MMDIT_MAP_BASIC:
        if k[1] in sd:
            new_sd[k[0]] = sd.pop(k[1])
    for k in sd:
        new_sd[k] = sd[k]
    sd = new_sd

    y_emb_shape = sd["y_embedder.mlp.0.weight"].shape
    depth = y_emb_shape[0] // 64
    hidden_size = 64 * depth
    num_heads = depth
    head_dim = hidden_size // num_heads
    num_blocks = comfy.model_detection.count_blocks(new_sd, 'transformer_blocks.{}.')

    load_device = comfy.model_management.get_torch_device()
    offload_device = comfy.model_management.unet_offload_device()
    unet_dtype = comfy.model_management.unet_dtype(model_params=-1)

    manual_cast_dtype = comfy.model_management.unet_manual_cast(unet_dtype, load_device)

    operations = model_options.get("custom_operations", None)
    if operations is None:
        operations = comfy.ops.pick_operations(unet_dtype, manual_cast_dtype, disable_fast_fp8=True)

    control_model = comfy.cldm.dit_embedder.ControlNetEmbedder(img_size=None,
                                                               patch_size=2,
                                                               in_chans=16,
                                                               num_layers=num_blocks,
                                                               main_model_double=depth,
                                                               double_y_emb=y_emb_shape[0] == y_emb_shape[1],
                                                               attention_head_dim=head_dim,
                                                               num_attention_heads=num_heads,
                                                               adm_in_channels=2048,
                                                               device=offload_device,
                                                               dtype=unet_dtype,
                                                               operations=operations)

    control_model = controlnet_load_state_dict(control_model, sd)

    latent_format = comfy.latent_formats.SD3()
    preprocess_image = lambda a: a
    if canny_cnet:
        preprocess_image = lambda a: (a * 255 * 0.5 + 0.5)
    elif depth_cnet:
        preprocess_image = lambda a: 1.0 - a

    control = ControlNetSD35(control_model, compression_ratio=1, latent_format=latent_format, load_device=load_device, manual_cast_dtype=manual_cast_dtype, preprocess_image=preprocess_image)
    return control