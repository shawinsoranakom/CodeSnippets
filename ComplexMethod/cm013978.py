def get_traced_fn(mod: Any) -> tuple[FunctionType, object | None]:
    """
    Utility function to get the function to trace, and optionally a bound self
    object, from a callable (nn.Module, function, or method).
    """
    import inspect

    if isinstance(mod, torch.nn.Module):
        resolved_forward = mod.forward
        if hasattr(resolved_forward, "__self__"):
            # pyrefly: ignore [missing-attribute]
            resolved_forward = resolved_forward.__func__

        resolved_call = mod.__call__
        if hasattr(resolved_call, "__self__"):
            resolved_call = resolved_call.__func__

        # Mirrored from NNModuleVariable.call_function:
        # https://github.com/pytorch/pytorch/blob/main/torch/_dynamo/variables/nn_module.py#L1035
        if (
            len(mod._forward_pre_hooks) == 0
            and len(mod._forward_hooks) == 0
            and len(torch.nn.modules.module._global_forward_pre_hooks) == 0
            and len(torch.nn.modules.module._global_forward_hooks) == 0
            and len(mod._backward_pre_hooks) == 0
            and len(mod._backward_hooks) == 0
            and len(torch.nn.modules.module._global_backward_pre_hooks) == 0
            and len(torch.nn.modules.module._global_backward_hooks) == 0
            and resolved_forward != torch.nn.Module.forward  # has forward impl
            and resolved_call == torch.nn.Module.__call__  # no custom __call__ impl
        ):
            # We cannot trace __call__ by default because it will break
            # the legacy dynamo export. If we want to revisit this,
            # feel free to remove this path and try unittests in
            # test_strict_export_v2.py
            mod = mod.forward
        elif isinstance(mod, torch.fx.GraphModule):
            mod = mod._call_impl
        else:
            mod = mod.__call__

    if hasattr(mod, "__self__"):
        return mod.__func__, mod.__self__
    elif inspect.isfunction(mod):
        return mod, None
    else:
        raise RuntimeError(f"Unsupported model code type {mod}")