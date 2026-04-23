def wrap_with_proxy(
        e: object, proxy: _NestedProxys, constant: _NestedTensors | None
    ) -> None:
        if isinstance(e, Tensor):
            if not isinstance(proxy, Proxy):
                raise AssertionError(f"Expected Proxy, got {type(proxy)}")
            if not (constant is None or isinstance(constant, Tensor)):
                raise AssertionError(f"Expected None or Tensor, got {type(constant)}")
            track_tensor(e, proxy, tracer=tracer, constant=constant)
            set_meta(proxy, e)
        elif isinstance(e, py_sym_types):
            if not isinstance(proxy, Proxy):
                raise AssertionError(f"Expected Proxy, got {type(proxy)}")
            # NB: eagerly set meta here, so that the numbering is in order
            set_meta(proxy, e)
            set_proxy_slot(e, tracer, thunkify(tracer, lambda: proxy))
        elif isinstance(e, _AnyScriptObject) or is_opaque_value(e):
            if not isinstance(proxy, Proxy):
                raise AssertionError(f"Expected Proxy, got {type(proxy)}")
            # Non-hoisted opaque value types should be baked as constants
            # in the graph, not tracked as proxy references. This matches
            # dynamo's behavior where non-hoisted values are not graph inputs.
            if (
                is_opaque_value_type(type(e))  # pyrefly: ignore[bad-argument-type]
                and not should_hoist(type(e))
            ):
                set_meta(proxy, e)
                return
            set_proxy_slot(e, tracer, proxy)
            set_meta(proxy, e)
        elif isinstance(e, (tuple, list)):
            # example use case: allreduce_ returns ([tensor], work)
            if isinstance(proxy, fx.Proxy):
                set_meta(proxy, e)

            def get_constant(
                c: _NestedTensors | None, idx: int
            ) -> _NestedTensors | None:
                if c is None:
                    return None
                else:
                    if not isinstance(c, (list, tuple)):
                        raise AssertionError(f"Expected list or tuple, got {type(c)}")
                    # pyrefly: ignore [bad-return]
                    return c[idx]

            for idx, ee in enumerate(e):
                # Use an indexer here - if proxy is a List then it will unwrap
                # it. If it's a Proxy then it will proxy the getelem.
                wrap_with_proxy(ee, proxy[idx], get_constant(constant, idx))  # type: ignore[index]

        elif isinstance(e, dict):
            # example use case: triton_kernel_wrapper takes arguments as kwargs

            # In theory we could support const-prop when proxy-tensor-tracing
            # operators that returns dicts of tensors, but we have no use case
            # for it today (since the only op we currently trace that can
            # return a dict is triton_kernel_wrapper_functional/mutation,
            # which does not participate in const-prop)
            if constant is not None:
                raise AssertionError("Expected constant to be None")

            if isinstance(proxy, fx.Proxy):
                set_meta(proxy, e)

            for key, val in e.items():
                wrap_with_proxy(val, proxy[key], None)  # type: ignore[index]

        elif isinstance(e, BackwardState):
            if not isinstance(proxy, Proxy):
                raise AssertionError(f"Expected Proxy, got {type(proxy)}")
            set_meta(proxy, e)
            e.proxy = proxy
        else:
            # intentionally pass on primitives
            pass