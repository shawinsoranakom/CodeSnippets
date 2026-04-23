def check_module_initialized(mod) -> None:
    if not isinstance(mod, torch.nn.Module):
        raise AssertionError(f"Expected torch.nn.Module, got {type(mod)}")
    if not hasattr(mod, "_parameters"):
        raise RuntimeError(
            f"'{torch.typename(type(mod))}' has not been initialized, did you forget to call 'super()'?"
        )

    # This is to avoid importing torch.distributed.nn
    if not hasattr(mod, "remote_parameters"):
        for name, param in mod._parameters.items():
            if param is not None and torch.nn.parameter.is_lazy(param):
                raise RuntimeError(
                    f"'{torch.typename(type(mod))}' has uninitialized parameters {name}. Did you forget to run a forward pass?"
                )
        for name, buf in mod._buffers.items():
            if buf is not None and torch.nn.parameter.is_lazy(buf):
                raise RuntimeError(
                    f"'{torch.typename(type(mod))}' has uninitialized buffers {name}. Did you forget to run a forward pass?"
                )