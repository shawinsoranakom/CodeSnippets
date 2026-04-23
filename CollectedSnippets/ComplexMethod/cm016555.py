def load_diffusion_model_state_dict(sd, model_options={}, metadata=None, disable_dynamic=False):
    """
    Loads a UNet diffusion model from a state dictionary, supporting both diffusers and regular formats.

    Args:
        sd (dict): State dictionary containing model weights and configuration
        model_options (dict, optional): Additional options for model loading. Supports:
            - dtype: Override model data type
            - custom_operations: Custom model operations
            - fp8_optimizations: Enable FP8 optimizations

    Returns:
        ModelPatcher: A wrapped model instance that handles device management and weight loading.
        Returns None if the model configuration cannot be detected.

    The function:
    1. Detects and handles different model formats (regular, diffusers, mmdit)
    2. Configures model dtype based on parameters and device capabilities
    3. Handles weight conversion and device placement
    4. Manages model optimization settings
    5. Loads weights and returns a device-managed model instance
    """
    dtype = model_options.get("dtype", None)

    custom_operations = model_options.get("custom_operations", None)
    if custom_operations is None:
        sd, metadata = comfy.utils.convert_old_quants(sd, "", metadata=metadata)

    #Allow loading unets from checkpoint files
    diffusion_model_prefix = model_detection.unet_prefix_from_state_dict(sd)
    temp_sd = comfy.utils.state_dict_prefix_replace(sd, {diffusion_model_prefix: ""}, filter_keys=True)
    if len(temp_sd) > 0:
        sd = temp_sd
        if custom_operations is None:
            sd, metadata = comfy.utils.convert_old_quants(sd, "", metadata=metadata)

    parameters = comfy.utils.calculate_parameters(sd)
    weight_dtype = comfy.utils.weight_dtype(sd)

    load_device = model_management.get_torch_device()
    model_config = model_detection.model_config_from_unet(sd, "", metadata=metadata)

    if model_config is not None:
        new_sd = sd
    else:
        new_sd = model_detection.convert_diffusers_mmdit(sd, "")
        if new_sd is not None: #diffusers mmdit
            model_config = model_detection.model_config_from_unet(new_sd, "")
            if model_config is None:
                return None
        else: #diffusers unet
            model_config = model_detection.model_config_from_diffusers_unet(sd)
            if model_config is None:
                return None

            diffusers_keys = comfy.utils.unet_to_diffusers(model_config.unet_config)

            new_sd = {}
            for k in diffusers_keys:
                if k in sd:
                    new_sd[diffusers_keys[k]] = sd.pop(k)
                else:
                    logging.warning("{} {}".format(diffusers_keys[k], k))

    offload_device = model_management.unet_offload_device()
    unet_weight_dtype = list(model_config.supported_inference_dtypes)
    if model_config.quant_config is not None:
        weight_dtype = None

    if dtype is None:
        unet_dtype = model_management.unet_dtype(model_params=parameters, supported_dtypes=unet_weight_dtype, weight_dtype=weight_dtype)
    else:
        unet_dtype = dtype

    if model_config.quant_config is not None:
        manual_cast_dtype = model_management.unet_manual_cast(None, load_device, model_config.supported_inference_dtypes)
    else:
        manual_cast_dtype = model_management.unet_manual_cast(unet_dtype, load_device, model_config.supported_inference_dtypes)
    model_config.set_inference_dtype(unet_dtype, manual_cast_dtype)

    if custom_operations is not None:
        model_config.custom_operations = custom_operations

    if model_options.get("fp8_optimizations", False):
        model_config.optimizations["fp8"] = True

    model = model_config.get_model(new_sd, "")
    ModelPatcher = comfy.model_patcher.ModelPatcher if disable_dynamic else comfy.model_patcher.CoreModelPatcher
    model_patcher = ModelPatcher(model, load_device=load_device, offload_device=offload_device)
    if not model_management.is_device_cpu(offload_device):
        model.to(offload_device)
    model.load_model_weights(new_sd, "", assign=model_patcher.is_dynamic())
    left_over = sd.keys()
    if len(left_over) > 0:
        logging.info("left over keys in diffusion model: {}".format(left_over))
    return model_patcher