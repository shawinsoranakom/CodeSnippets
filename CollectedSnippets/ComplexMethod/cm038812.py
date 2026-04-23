def construct_marker_dict_and_push(
    module_name, module_obj, in_tensor, kwargs=None, out_tensor=None
):
    marker_dict = {}
    marker_dict["Module"] = module_name

    ## Get trainable parameters like weights and bias
    module_params = module_obj.named_parameters(recurse=False)
    for idx, (param_name, param_obj) in enumerate(module_params):
        if idx == 0:
            marker_dict["TrainableParams"] = {}
        marker_dict["TrainableParams"][param_name] = list(param_obj.size())

    in_tensor_list = print_tensor(in_tensor, "Input")
    if in_tensor_list:
        marker_dict["Inputs"] = in_tensor_list

    out_tensor_list = print_tensor(out_tensor, "Output")
    if out_tensor_list:
        marker_dict["Outputs"] = out_tensor_list

    ## Get Kwargs like input_ids and positions for the top module
    if kwargs:
        for key, value in kwargs.items():
            if isinstance(value, (torch.Tensor, list, tuple)):
                tensor_list = print_tensor(value, key)
                if tensor_list:
                    marker_dict[key] = tensor_list

    param_info = process_layer_params(module_obj)
    if param_info:
        marker_dict["StaticParams"] = param_info
    nvtx.range_push("{}".format(marker_dict))