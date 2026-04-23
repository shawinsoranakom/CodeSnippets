def set_tensor(module: "torch.nn.Module", name: str, tensor: torch.Tensor) -> None:
    if not isinstance(module, torch.nn.Module):
        raise TypeError(f"{module} is not an instance of torch.nn.Module")
    if not isinstance(tensor, torch.Tensor) and tensor is not None:
        raise TypeError(f"{tensor} is not an instance of torch.Tensor")
    if "." in name:
        raise KeyError('tensor name can\'t contain "."')
    if name == "":
        raise KeyError('tensor name can\'t be empty string ""')
    if name in module._parameters:
        module._parameters[name] = tensor  # type: ignore[assignment]
    elif name in module._buffers:
        module._buffers[name] = tensor
    else:
        setattr(module, name, tensor)