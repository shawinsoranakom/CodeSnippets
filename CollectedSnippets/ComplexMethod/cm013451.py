def set_proxy_slot(
    obj: PySymType | _AnyScriptObjectType | Tensor | OpaqueBase,
    tracer: _ProxyTracer,
    proxy: object,
) -> None:
    log.debug("set_proxy_slot %s (%s) %s", obj, id(obj), proxy)
    if isinstance(obj, Tensor):
        # We DO want to clobber proxies whenever we run an inplace operation
        # on a tensor, and it affects the metadata on the proxy.
        if not isinstance(proxy, _ProxyTensor):
            raise AssertionError(f"Expected _ProxyTensor, got {type(proxy)}")
        # see NOTE [Do not clobber inplace ops]
        if (
            obj not in tracer.tensor_tracker
            or not _is_proxy_tensor_update_tensor_tracker_disabled()
        ):
            tracer.tensor_tracker[obj] = proxy
    elif isinstance(obj, (_AnyScriptObject)) or is_opaque_value(obj):
        if not isinstance(proxy, Proxy):
            raise AssertionError(f"Expected Proxy, got {type(proxy)}")
        # ScriptObject (actual C++ torchbind) uses _WeakHashRef-keyed tracker
        # because the same C++ IValue can produce different Python wrappers.
        # FakeScriptObject/OpaqueBase uses WeakIdRef-keyed tracker because
        # value-equal objects (e.g. primal vs tangent) must be tracked separately.
        if isinstance(obj, torch.ScriptObject):
            tracer.script_object_tracker[obj] = proxy
        else:
            # NB: Never clobber a pre-existing proxy for the same
            # underlying real object.  Multiple FakeScriptObject wrappers
            # can share the same real_obj (e.g. primal vs tangent
            # placeholders during joint graph tracing).  We always keep the
            # first proxy registered, with the same rationale as the
            # symnode_tracker first-one-wins policy below: primals are
            # registered first, so this avoids spurious tangent dependencies
            # in forward outputs (which would break the partitioner).
            real_obj = None
            if isinstance(obj, FakeScriptObject):
                try:
                    real_obj = object.__getattribute__(obj, "real_obj")
                except AttributeError:
                    pass

            if real_obj is not None:
                existing = tracer._opaque_real_obj_proxy.get(id(real_obj))
                if existing is not None:
                    tracer.opaque_tracker[obj] = existing
                else:
                    tracer.opaque_tracker[obj] = proxy
                    tracer._opaque_real_obj_proxy[id(real_obj)] = proxy
            else:
                tracer.opaque_tracker[obj] = proxy
    else:
        # NB: Never clobber pre-existing proxy.  Although the proxies
        # are in principle equivalent, when we do graph partitioning
        # we need there not to be spurious dependencies on tangent inputs.
        # This works because primals get their SymInts set first, and
        # THEN later we allocate tangent inputs.  Make sure if a SymInt
        # is derivable from a primal that we use that.
        if not isinstance(obj, py_sym_types):
            raise AssertionError(f"Expected py_sym_types, got {type(obj)}")
        if obj not in tracer.symnode_tracker:
            proxy = typing.cast(_PySymProxyType, proxy)
            tracer.symnode_tracker[obj] = proxy

            # WAR: python test/dynamo/test_subclasses.py
            # TestNestedTensor.test_basic_autograd
            #
            # AOTAutograd doesn't pass the "outer sizes" as an actual argument
            # to make_fx, but it is made use of internally in AOTAutograd's
            # call to tensor unflatten.  Because the outer sizes isn't passed
            # as an argument, it is therefore untracked.  However, it turns
            # out you luck out, because *Dynamo* will manually add the outer
            # sizes as an argument so you can fix up the proxy'ness.
            #
            # This is probably fixed in
            # https://github.com/pytorch/pytorch/pull/125941/
            import sympy

            if isinstance(obj.node.expr, sympy.Symbol):
                tracer.sympy_expr_tracker[obj.node.expr] = _SympyExprTrackerValue(
                    proxy, obj
                )