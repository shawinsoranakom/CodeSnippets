def process_layer_params(module_obj):
    """Extract the static parameters from LLM and VLM relevant layer types"""
    param_info = {}
    # Extract parameters for layers commonly used in LLMs and VLMs
    if isinstance(module_obj, (torch.nn.Conv1d, torch.nn.Conv2d, torch.nn.Conv3d)):
        conv_params = {}
        conv_params["in_chan"] = module_obj.in_channels
        conv_params["out_chan"] = module_obj.out_channels
        conv_params["filter_dim"] = module_obj.kernel_size
        conv_params["stride"] = module_obj.stride
        conv_params["padding"] = module_obj.padding
        conv_params["dilation"] = module_obj.dilation
        conv_params["transposed"] = module_obj.transposed
        conv_params["output_padding"] = module_obj.output_padding
        conv_params["groups"] = module_obj.groups
        conv_params["padding_mode"] = module_obj.padding_mode
        param_info = conv_params
    elif isinstance(
        module_obj,
        (
            torch.nn.ConvTranspose1d,
            torch.nn.ConvTranspose2d,
            torch.nn.ConvTranspose3d,
        ),
    ):
        convtranspose_params = {}
        convtranspose_params["in_chan"] = module_obj.in_channels
        convtranspose_params["out_chan"] = module_obj.out_channels
        convtranspose_params["filter_dim"] = module_obj.kernel_size
        convtranspose_params["stride"] = module_obj.stride
        convtranspose_params["padding"] = module_obj.padding
        convtranspose_params["dilation"] = module_obj.dilation
        convtranspose_params["transposed"] = module_obj.transposed
        convtranspose_params["output_padding"] = module_obj.output_padding
        convtranspose_params["groups"] = module_obj.groups
        convtranspose_params["padding_mode"] = module_obj.padding_mode
        param_info = convtranspose_params
    elif isinstance(
        module_obj, (torch.nn.MaxPool1d, torch.nn.MaxPool2d, torch.nn.MaxPool3d)
    ):

        def _handle_int_or_tuple(parameter):
            if isinstance(parameter, tuple):
                return list(parameter)
            elif isinstance(parameter, int):
                return [parameter, parameter]

        pooling_params = {}
        pooling_params["filter_dim"] = _handle_int_or_tuple(module_obj.kernel_size)
        pooling_params["stride"] = _handle_int_or_tuple(module_obj.stride)
        pooling_params["padding"] = _handle_int_or_tuple(module_obj.padding)
        pooling_params["dilation"] = _handle_int_or_tuple(module_obj.dilation)
        param_info = pooling_params
    elif isinstance(
        module_obj, (torch.nn.AvgPool1d, torch.nn.AvgPool2d, torch.nn.AvgPool3d)
    ):
        pooling_params = {}
        pooling_params["filter_dim"] = [
            module_obj.kernel_size,
            module_obj.kernel_size,
        ]
        pooling_params["stride"] = [module_obj.stride, module_obj.stride]
        pooling_params["padding"] = [module_obj.padding, module_obj.padding]
        pooling_params["ceil_mode"] = module_obj.ceil_mode
        pooling_params["count_include_pad"] = module_obj.count_include_pad
        param_info = pooling_params
    elif isinstance(
        module_obj,
        (
            torch.nn.AdaptiveAvgPool1d,
            torch.nn.AdaptiveAvgPool2d,
            torch.nn.AdaptiveAvgPool3d,
        ),
    ):
        pooling_params = {}
        pooling_params["output_size"] = [
            module_obj.output_size,
            module_obj.output_size,
        ]
        param_info = pooling_params
    elif isinstance(module_obj, torch.nn.Linear):
        param_info["in_features"] = module_obj.in_features
        param_info["out_features"] = module_obj.out_features
    elif isinstance(
        module_obj,
        (torch.nn.BatchNorm1d, torch.nn.BatchNorm2d, torch.nn.BatchNorm3d),
    ):
        param_info["num_features"] = module_obj.num_features
        param_info["epsilon"] = module_obj.eps
        param_info["momentum"] = module_obj.momentum
    elif isinstance(module_obj, torch.nn.ReLU):
        param_info["in_place"] = module_obj.inplace
    elif isinstance(module_obj, torch.nn.Dropout):
        param_info["p"] = module_obj.p
        param_info["in_place"] = module_obj.inplace
    elif isinstance(module_obj, torch.nn.Embedding):
        param_info["num_embeddings"] = module_obj.num_embeddings
        param_info["embedding_dim"] = module_obj.embedding_dim
    elif isinstance(
        module_obj,
        (
            torch.nn.Upsample,
            torch.nn.UpsamplingNearest2d,
            torch.nn.UpsamplingBilinear2d,
        ),
    ):
        param_info["scale_factor"] = module_obj.scale_factor

    return param_info