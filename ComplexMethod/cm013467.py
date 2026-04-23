def module_to_nested_dict(module: torch.nn.Module) -> dict[str, Any]:
    """Recursively converts an nn.Module into a nested dictionary with explicit 'parameters' and 'modules' keys."""
    self_dict: dict[str, Any] = {}

    parameters: dict[str, torch.Tensor] = {}
    modules: dict[str, dict[str, Any]] = {}
    self_dict["_parameters"] = parameters
    self_dict["_modules"] = modules

    for attr_name in dir(module):
        try:
            if not attr_name.startswith("_") and not callable(
                getattr(module, attr_name)
            ):
                attr_value = getattr(module, attr_name)
                if (
                    not isinstance(attr_value, torch.nn.Module)
                    and isinstance(attr_value, (int, float, torch.Tensor))
                    and type(attr_value) is not bool
                ):
                    self_dict[attr_name] = attr_value
        except NotImplementedError:
            # Skip attributes that raise NotImplementedError since they won't
            # contain any dynamism anyways.
            continue

    for name, param in module.named_parameters(recurse=False):
        self_dict["_parameters"][name] = param
    for name, buffer in module.named_buffers(recurse=False):
        self_dict["_parameters"][name] = buffer

    for name, submodule in module.named_children():
        self_dict["_modules"][name] = module_to_nested_dict(submodule)

    return self_dict