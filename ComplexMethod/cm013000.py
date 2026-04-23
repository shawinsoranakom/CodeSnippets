def disable_apex_o2_state_dict_hook(model: torch.nn.Module | torch.jit.ScriptFunction):
    """A context manager to temporarily disable the Apex O2 hook that returns.

    .. deprecated:: 2.7
        Please remove usage of this function.
    """
    # Apex O2 hook state_dict to return fp16 weights as fp32.
    # Exporter cannot identify them as same tensors.
    # Since this hook is only used by optimizer, it is safe to
    # remove this hook while exporting.
    if not isinstance(model, torch.jit.ScriptFunction):
        model_hooks = {}  # type: ignore[var-annotated]
        for module in model.modules():
            for key, hook in module._state_dict_hooks.items():
                if type(hook).__name__ == "O2StateDictHook":
                    if module not in model_hooks:
                        model_hooks[module] = {}
                    model_hooks[module][key] = hook
            if module in model_hooks:
                for key in model_hooks[module]:
                    module._state_dict_hooks.pop(key)
        try:
            yield
        finally:
            # Add the hooks back
            for module, m_map in model_hooks.items():
                for key, hook in m_map.items():
                    module._state_dict_hooks[key] = hook
    else:
        try:
            yield
        finally:
            pass