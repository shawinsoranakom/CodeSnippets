def _assign_attr(
    from_obj: torch.Tensor | torch.ScriptObject | torch.nn.Module,
    to_module: torch.nn.Module,
    target: str,
    attr_kind: _AttrKind,
    persistent: bool = True,
):
    *prefix, field = target.split(".")
    # We need to generate all submodules of `to_module` that are at `prefix` and
    # variants of `prefix` that differ only by call name. All of these submodules
    # will then be assigned `from_obj` at `field` so that they can share this attribute.
    # For example, if target is foo.bar.f, foo has another call name foo@1,
    # and bar has other call names bar@1, bar@2, then we will assign f to
    # foo.bar, foo.bar@1, foo.bar@2, foo@1.bar, foo@1.bar@1, foo@1.bar@2.
    to_modules = {to_module}
    for item in prefix:
        ts: set[torch.nn.Module] = set()
        for to_module in to_modules:
            if not hasattr(to_module, item):
                setattr(to_module, item, torch.nn.Module())
            ts.update(
                t_call  # type: ignore[misc]
                for k, t_call in to_module._modules.items()
                if _is_call_name(k, item)
            )
        to_modules = ts

    for to_module in to_modules:
        if attr_kind == _AttrKind.PARAMETER:
            if not isinstance(from_obj, torch.nn.Parameter):
                raise AssertionError(
                    f"expected torch.nn.Parameter for PARAMETER attr_kind, got {type(from_obj)}"
                )
            to_module.register_parameter(field, from_obj)
        elif attr_kind == _AttrKind.BUFFER:
            if not isinstance(from_obj, torch.Tensor):
                raise AssertionError(
                    f"expected torch.Tensor for BUFFER attr_kind, got {type(from_obj)}"
                )
            to_module.register_buffer(field, from_obj, persistent=persistent)
        elif attr_kind == _AttrKind.CONSTANT:
            if isinstance(from_obj, FakeScriptObject):
                raise AssertionError(
                    "FakeScriptObject should only exist during tracing."
                )
            if not isinstance(
                from_obj,
                (
                    torch.Tensor,
                    torch.ScriptObject,
                ),
            ):
                raise AssertionError(
                    f"expected torch.Tensor or torch.ScriptObject for CONSTANT attr_kind, got {type(from_obj)}"
                )
            setattr(to_module, field, from_obj)
        elif attr_kind == _AttrKind.MODULE:
            if not isinstance(from_obj, torch.nn.Module):
                raise AssertionError(
                    f"expected torch.nn.Module for MODULE attr_kind, got {type(from_obj)}"
                )
            setattr(to_module, field, from_obj)