def get_proxy_slot(
    obj: Tensor | _AnyScriptObjectType | PySymType | OpaqueBase,
    tracer: _ProxyTracer,
    default: object = no_default,
    transform: Callable[..., Any] = lambda x: x,
) -> object:
    tracker: Any
    if isinstance(obj, Tensor):
        tracker = tracer.tensor_tracker
    elif isinstance(obj, _AnyScriptObject) or is_opaque_value(obj):
        if isinstance(obj, torch.ScriptObject):
            tracker = tracer.script_object_tracker
        else:
            tracker = tracer.opaque_tracker
    else:
        if not isinstance(obj, py_sym_types):
            raise AssertionError(f"Expected py_sym_types, got {type(obj)}")
        tracker = tracer.symnode_tracker

    # pyrefly: ignore [index-error]
    # pyrefly: ignore [no-matching-overload, bad-argument-type]
    value = tracker.get(obj)

    if value is None and isinstance(obj, py_sym_types):
        if obj.node.is_symbolic():
            # Last ditch - we found a SymInt (SymBool, etc) we don't know
            # about.
            if (tmp := tracer.sympy_expr_tracker.get(obj.node.expr)) is not None:
                value = tmp.proxy

            else:
                # Attempt to build it from first principles.
                _build_proxy_for_sym_expr(tracer, obj.node.expr, obj)
                # pyrefly: ignore [bad-argument-type, no-matching-overload]
                value = tracker.get(obj)

    if value is None and isinstance(obj, FakeScriptObject):
        # A new FakeScriptObject wrapping the same real_obj may have been
        # created (e.g. output flattening in unwrap_tensor_subclasses calls
        # maybe_to_fake_obj which always mints a fresh wrapper).  Fall back
        # to the real-object dedup map that set_proxy_slot maintains.
        value = tracer._opaque_real_obj_proxy.get(id(obj.real_obj))

    if value is None:
        # We don't know this value - return the default.
        if isinstance(default, _NoDefault):
            raise RuntimeError(
                f"{obj} ({type(obj)}, {id(obj)})is not tracked with proxy for {tracer}"
            )
        return default

    res = transform(value)
    return res