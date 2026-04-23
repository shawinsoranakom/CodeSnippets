def swap_module(
    mod: nn.Module, mapping: dict[type[nn.Module], type[nn.Module]]
) -> nn.Module:
    r"""Swaps the module using from_dense according to the mapping passed in.
    Args:
        mod: input module
        mapping: a dictionary that maps from nn module to sparse nn module
    Return:
        The corresponding sparse module of `mod` according to mapping, created using from_dense
    """
    if type_before_parametrizations(mod) in mapping:
        sparse_mod = mapping[type_before_parametrizations(mod)]

        # TODO Fix this typing, as Type[Module] has no attribute "from_dense"
        new_mod = sparse_mod.from_dense(mod)  # type: ignore[attr-defined]

        # Preserve module's pre forward hooks. They'll be called on quantized input
        for pre_hook_fn in mod._forward_pre_hooks.values():
            new_mod.register_forward_pre_hook(pre_hook_fn)
        # Preserve module's post forward hooks except _observer_forward_hook
        # After convert they'll work with quantized output
        for hook_fn in mod._forward_hooks.values():
            new_mod.register_forward_hook(hook_fn)

        # respect device affinity when swapping modules
        # pyrefly: ignore [bad-argument-type]
        devices = {p.device for p in chain(mod.parameters(), mod.buffers())}
        if len(devices) > 1:
            raise AssertionError(
                f"swap_module only works with cpu or single-device CUDA modules, but got devices {devices}"
            )
        device = next(iter(devices)) if len(devices) > 0 else None
        if device:
            new_mod.to(device)

        return new_mod

    else:
        return mod