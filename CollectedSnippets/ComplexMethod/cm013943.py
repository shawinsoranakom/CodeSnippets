def mark_static(t: Any, index: int | list[Any] | tuple[Any] | None = None) -> None:
    """
    Mark a tensor as having a static dim or mark a nn module class as static.

    For tensors
    ===========
    This will prevent us from attempting to compile it dynamically
    when dynamic=True; this can improve trace-time performance.

    This has lower precedence than mark_dynamic.

    Unlike mark_dynamic, this can be done inside a graph, in which case it
    induces specialization on the tensor.

    For nn.Module classes
    =====================
    For static nn.Module classes, TorchDynamo assumes that the module instance
    attributes will not be modified after compilation. This will ensure that
    TorchDynamo keeps integer attributes CONSTANT and not symints.

    From TorchDynamo implementation side, the instances of static-marked
    nn.Module class will be converted to UnspecializedBuiltinNNModuleVariable,
    which have the same properties.

    Note that we still have to guard on the attributes, because different
    instances of the nn.Module can have different values of the attributes. The
    key point here is that the attributes are static.
    """
    if is_compiling():
        if index is None:
            for s in t.size():
                comptime.force_static(s)
        else:
            comptime.force_static(t.size(index))
        return

    if is_traceable_wrapper_subclass(t):
        # default behavior: mirror mark_static() on all inner tensors with same dim as t
        # TODO: Make this configurable via a supported public API
        _apply_func_to_inner_tensors_of_same_dim(mark_static, t, index)

    if not isinstance(t, torch.Tensor) and issubclass(t, torch.nn.Module):
        t._dynamo_marked_static = True
        # pyrefly: ignore [bad-return]
        return t

    if not isinstance(t, torch.Tensor):
        raise TypeError(
            f"mark_static expects a tensor/nn.Module class but received {type(t)}"
        )

    if isinstance(index, int):
        if not hasattr(t, "_dynamo_static_indices"):
            t._dynamo_static_indices = set()  # type: ignore[attr-defined]
        # TODO(voz): Should we bounds check?
        t._dynamo_static_indices.add(index)  # type: ignore[attr-defined]
    elif index is None:
        for i in range(t.dim()):
            mark_static(t, i)
    else:
        assert isinstance(index, (list, tuple))
        for i in index:
            mark_static(t, i)