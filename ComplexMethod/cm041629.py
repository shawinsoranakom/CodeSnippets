def get_transformer_layer_cls(model: HFModel) -> type[nn.Module] | None:
    no_split_modules = getattr(model, "_no_split_modules", None)
    if no_split_modules:
        if isinstance(no_split_modules, (list, tuple)):
            for name, module in model.named_modules():
                for cls_name in no_split_modules:
                    if module.__class__.__name__ == cls_name:
                        return module.__class__
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return type(model.model.layers[0])
    if hasattr(model, "layers"):
        return type(model.layers[0])

    return None