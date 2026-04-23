def _make_prim(
    *,
    schema: str,
    return_type: RETURN_TYPE | tuple[RETURN_TYPE, ...],
    meta: Callable,
    impl_aten: Callable,
    doc: str,
    tags: Sequence[torch.Tag] | None = None,
    use_old_custom_ops_api: bool = False,
    register_conj_neg_fallthrough: bool = False,
):
    """
    Creates a primitive operation.

    """

    def _prim_impl(*args, **kwargs):
        # always run the meta function because aten implementation will
        # typically accept more inputs (e.g., it will do promotion and
        # broadcasting) which we want to reject
        meta(*args, **kwargs)
        return impl_aten(*args, **kwargs)

    # Right now prims don't support autograd (we can and should add an
    # argument that provides an implementation for backward here.)  Because we
    # don't have derivative formulas, we must setup a custom autograd function
    # that raises an error if backwards is invoked
    def _autograd_impl(*args, **kwargs):
        return backwards_not_supported(_prim)(*args, **kwargs)

    def _backend_select_impl(*args, **kwargs):
        if kwargs.get("device") and kwargs["device"].type == "meta":
            return meta(*args, **kwargs)
        if any(isinstance(x, torch.device) and x.type == "meta" for x in args):
            return meta(*args, **kwargs)
        else:
            return _prim_impl(*args, **kwargs)

    name = schema.split("(", maxsplit=1)[0]
    schema = schema[len(name) :]

    # register non-functional ops with old custom ops API
    cpp_schema = torch._C.parse_schema(name + schema)
    if use_old_custom_ops_api or not is_functional_schema(cpp_schema):
        prim.define(name + schema, tags=torch.Tag.pt2_compliant_tag)
        prim_impl.impl(name, _prim_impl)
        prim_autograd_impl.impl(name, _autograd_impl)
        prim_meta_impl.impl(name, meta)
    else:
        mutates_args = [
            arg.name
            for arg in cpp_schema.arguments
            if arg.alias_info is not None and arg.alias_info.is_write
        ]
        prim_def = torch.library.custom_op(
            "prims::" + name,
            _prim_impl,
            mutates_args=tuple(mutates_args),
            schema=schema,
        )
        prim_def.register_fake(meta)

        # all view ops get conj/neg fallthroughs
        if return_type == RETURN_TYPE.VIEW or register_conj_neg_fallthrough:
            prim_def._lib.impl(name, torch.library.fallthrough_kernel, "Conjugate")
            prim_def._lib.impl(name, torch.library.fallthrough_kernel, "Negative")

    _prim_packet = getattr(torch._ops.ops.prims, name)
    _prim = _prim_packet.default
    if tags:
        _prim._tags = tags
    elif aten_packet := getattr(torch.ops.aten, name, None):
        overload_tags = [
            getattr(aten_packet, overload).tags for overload in aten_packet.overloads()
        ]
        tags_intersection = set(overload_tags[0])
        tags_intersection.intersection_update(*overload_tags[1:])

        # dont inadvertently add to prim ops
        tags_intersection.discard(torch.Tag.core)
        # causes errors with python ref executor tests, none of the
        # data dependent pytorch ops actually decompose to prims
        tags_intersection.discard(torch.Tag.data_dependent_output)

        # iter over first tags for determinism
        _prim._tags = tuple(t for t in overload_tags[0] if t in tags_intersection)

    from torch._subclasses.fake_tensor import contains_tensor_types

    if (
        not any(contains_tensor_types(a.type) for a in _prim._schema.arguments)
        or str(
            _prim
            # See https://github.com/pytorch/pytorch/issues/103532
        )
        == "prims.device_put.default"
    ):
        prim_backend_select_impl.impl(name, _backend_select_impl)

    for p in (_prim_packet, _prim):
        p.__doc__ = doc
        p.return_type = return_type  # type: ignore[attr-defined]

        p.schema = schema
        p.prim_impl = _prim_impl
        p.prim_meta_impl = meta
        p.impl_aten = impl_aten

    return _prim