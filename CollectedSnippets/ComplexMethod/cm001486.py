def hypertile_hook_model(model: nn.Module, width, height, *, enable=False, tile_size_max=128, swap_size=1, max_depth=3, is_sdxl=False):
    hypertile_layers = getattr(model, "__webui_hypertile_layers", None)
    if hypertile_layers is None:
        if not enable:
            return

        hypertile_layers = {}
        layers = DEPTH_LAYERS_XL if is_sdxl else DEPTH_LAYERS

        for depth in range(4):
            for layer_name, module in model.named_modules():
                if any(layer_name.endswith(try_name) for try_name in layers[depth]):
                    params = HypertileParams()
                    module.__webui_hypertile_params = params
                    params.forward = module.forward
                    params.depth = depth
                    params.layer_name = layer_name
                    module.forward = self_attn_forward(params)

                    hypertile_layers[layer_name] = 1

        model.__webui_hypertile_layers = hypertile_layers

    aspect_ratio = width / height
    tile_size = min(largest_tile_size_available(width, height), tile_size_max)

    for layer_name, module in model.named_modules():
        if layer_name in hypertile_layers:
            params = module.__webui_hypertile_params

            params.tile_size = tile_size
            params.swap_size = swap_size
            params.aspect_ratio = aspect_ratio
            params.enabled = enable and params.depth <= max_depth