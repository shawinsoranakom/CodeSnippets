def _prepare_for_hqq_linear(model, patch_params, has_been_replaced, current_key_name=None):
    for name, module in model.named_children():
        if current_key_name is None:
            current_key_name = []
        current_key_name.append(name)

        if isinstance(module, torch.nn.Linear):
            # Get linear tag
            linear_tag = name_to_linear_tag(module.name)

            # We put the module quant_config into the nn.Linear layer so we can access it later in quantizer_hqq.create_quantized_param()
            if linear_tag in patch_params:
                if patch_params[linear_tag] is not None:
                    model._modules[name].quant_config = patch_params[linear_tag]
                    # Store the module class in case we need to transpose the weight later
                    model._modules[name].source_cls = type(module)
                    # Force requires grad to False to avoid unexpected errors
                    model._modules[name].requires_grad_(False)

            has_been_replaced = True

            # Add these fake parameters to avoid loading fail
            for att in ["W_q", "meta"]:
                setattr(module, att, None)

        if len(list(module.children())) > 0:
            _, has_been_replaced = _prepare_for_hqq_linear(
                module,
                patch_params=patch_params,
                has_been_replaced=has_been_replaced,
            )
        # Remove the last key for recursion
        current_key_name.pop(-1)

    return model, has_been_replaced