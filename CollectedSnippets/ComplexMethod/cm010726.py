def maybe_to_fake_obj(
    fake_mode,
    x: Any,
) -> FakeScriptObject | torch.ScriptObject:
    import torch.utils._pytree as pytree

    # When tracing with real mode, people should implement meta kernels that can
    # handle the case of real script object + fake tensor inputs.
    if tracing_with_real(x):
        return x

    from torch._library.opaque_object import (
        FakeOpaqueObject,
        get_opaque_obj_info,
        get_opaque_type_name,
        is_opaque_type,
        OpaqueTypeStr,
    )

    x_type = type(x)
    if is_opaque_type(x_type):
        type_name = OpaqueTypeStr if x is None else get_opaque_type_name(x_type)
        fake_x_wrapped = FakeScriptObject(FakeOpaqueObject(), type_name, x)

        # Set specified members onto the fake object
        opaque_info = get_opaque_obj_info(x_type)
        if opaque_info is None:
            raise AssertionError(f"opaque_info for type {x_type} must not be None")
        for attr_name in opaque_info.members:
            with _disable_current_modes():
                if not hasattr(x, attr_name):
                    raise TypeError(
                        f"Opaque object of type '{type_name}' was specified to have member "
                        f"'{attr_name}', but this doesn't actually exist in the object."
                    )
                object.__setattr__(fake_x_wrapped, attr_name, getattr(x, attr_name))

        return fake_x_wrapped
    else:
        # x.__obj_flatten__() could be calling some tensor operations inside but we don't
        # want to call these ops in surrounding dispatch modes when executing it.
        # Otherwise, for example, the fake tensor modes will error out when the tensors inside
        # script object execute some operations like clone if allow_non_fake_input flag is set.
        with _disable_current_modes():
            flat_x = x.__obj_flatten__()  # type: ignore[attr-defined]

        _check_valid_flat_script_obj(flat_x)

        with fake_mode:
            from torch._higher_order_ops.utils import _tensor_storage

            storage_map = {
                _tensor_storage(inp): i
                for i, inp in enumerate(flat_x)
                if isinstance(inp, torch.Tensor)
            }
            alias_map = {
                i: storage_map[_tensor_storage(inp)]
                for i, inp in enumerate(flat_x)
                if isinstance(inp, torch.Tensor)
                and storage_map[_tensor_storage(inp)] != i
            }
            if len(alias_map) > 0:
                log.warning(
                    "Detected script object %s has aliasing relationship among its tensors. "
                    "Flattened obj: %s. Aliasing tensor indices: %s. "
                    "This is not supported and may cause unexpected behavior.",
                    x,
                    flat_x,
                    alias_map,
                )

            # This breaks the aliasing relationship among the tensors inside the torchbind object
            # This is bad but since we don't need to preserve the aliasing relationship anyway and
            # we state clearly that aliasing relationship is not preserved in the doc so this might be OK.
            fake_flattened = pytree.tree_map_only(
                torch.Tensor,
                lambda t: torch.empty_strided(
                    t.size(),
                    t.stride(),
                    device=t.device,
                    dtype=t.dtype,
                    requires_grad=t.requires_grad,
                    layout=t.layout,
                ),
                flat_x,
            )

        fake_x = _find_fake_class_for_script_object(x).__obj_unflatten__(fake_flattened)

    fake_x_wrapped = FakeScriptObject(fake_x, x._type().qualified_name(), x)  # type: ignore[attr-defined]

    for name in x._method_names():  # type: ignore[attr-defined]
        attr = getattr(fake_x, name, None)
        if attr is not None:
            if not callable(attr):
                raise RuntimeError(f"Expect {name} to be a callable but got {attr}.")

            real_attr = getattr(x, name)  # type: ignore[attr-defined]

            # real attr sometimes is not torch.ScriptMethod thus doesn't have schema e.g. __init___ or __eq__
            method_schema: torch.FunctionSchema | None = None
            if isinstance(real_attr, torch.ScriptMethod):
                method_schema = real_attr.schema  # type: ignore[attr-defined]

            # Bypasses our custom setattr function
            object.__setattr__(
                fake_x_wrapped,
                name,
                FakeScriptMethod(fake_x_wrapped, name, method_schema),
            )
        else:
            override_skip_list = {"__obj_flatten__", "__getstate__", "__setstate__"}
            if name not in override_skip_list:
                log.warning("fake object of %s doesn't implement method %s.", x, name)
    return fake_x_wrapped