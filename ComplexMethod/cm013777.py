def swap_tensor(
    module: "torch.nn.Module",
    name: str,
    tensor: torch.Tensor,
    allow_missing: bool = False,
) -> torch.Tensor:
    if not isinstance(module, torch.nn.Module):
        raise TypeError(f"{module} is not an instance of torch.nn.Module")
    if (
        tensor is not _MISSING
        and not isinstance(tensor, torch.Tensor)
        and tensor is not None
    ):
        raise TypeError(f"{tensor} is not an instance of torch.Tensor")
    if "." in name:
        raise KeyError('tensor name can\'t contain "."')
    if name == "":
        raise KeyError('tensor name can\'t be empty string ""')

    orig_tensor: torch.Tensor
    if name in module._parameters:
        orig_tensor = module._parameters[name]  # type: ignore[assignment]
        if tensor is not _MISSING:
            module._parameters[name] = tensor  # type: ignore[assignment]
        else:
            del module._parameters[name]
    elif name in module._buffers:
        orig_tensor = module._buffers[name]  # type: ignore[assignment]
        if tensor is not _MISSING:
            module._buffers[name] = tensor
        else:
            del module._buffers[name]
    else:
        if hasattr(module, name):
            orig_tensor = getattr(module, name)
        else:
            if not allow_missing:
                raise AttributeError(f"{module._get_name()} has no attribute `{name}`")
            orig_tensor = _MISSING
        if (
            orig_tensor is not _MISSING
            and not isinstance(orig_tensor, torch.Tensor)
            and orig_tensor is not None
        ):
            raise TypeError(
                f"attribute `{name}`: {orig_tensor} is not an instance of torch.Tensor"
            )
        if tensor is not _MISSING:
            setattr(module, name, tensor)
        elif hasattr(module, name):
            delattr(module, name)
    # pyrefly: ignore [bad-return]
    return orig_tensor