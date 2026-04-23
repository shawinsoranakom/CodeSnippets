def like_factory_default(func, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    inp = new_kwargs.pop("input")

    # Default layout is technically torch.strided but only jagged is supported here.
    # Rather than force users to specify the layout, assume jagged.
    # This should be set to strided for redispatching on values.
    new_kwargs["layout"] = torch.strided

    new_values = func(inp._values, **new_kwargs)
    new_offsets = inp._offsets.to(device=new_values.device)
    new_lengths = None
    if inp._lengths is not None:
        new_lengths = inp._lengths.to(device=new_values.device)
    output_kwargs = extract_kwargs(inp)
    if "offsets" in output_kwargs:
        output_kwargs["offsets"] = new_offsets
    if "lengths" in output_kwargs:
        output_kwargs["lengths"] = new_lengths

    if inp.device != new_values.device:
        # Update the nested int registry to indicate that the ragged structure is the same
        # between the two offsets / lengths on different devices.
        from torch._subclasses.fake_tensor import FakeTensor
        from torch._subclasses.functional_tensor import (
            FunctionalTensor,
            mb_unwrap_functional_tensor,
        )

        from .nested_tensor import _tensor_symint_registry

        ragged_source = inp._offsets if inp._lengths is None else inp._lengths
        new_thing = new_offsets if new_lengths is None else new_lengths
        if isinstance(new_thing, (FakeTensor, FunctionalTensor)):
            # Temporary hack until we have the union find
            tgt = mb_unwrap_functional_tensor(new_thing)
            src = mb_unwrap_functional_tensor(ragged_source)
            # pyrefly: ignore[missing-attribute]
            tgt.nested_int_memo = src.nested_int_memo
        else:
            _tensor_symint_registry[new_thing] = _tensor_symint_registry[ragged_source]

    return NestedTensor(new_values, **output_kwargs)