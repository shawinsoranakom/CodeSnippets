def _dispatch_impl(
        self,
        func: OpOverload,
        types: Sequence[type],
        args: Sequence[object],
        kwargs: Mapping[str, object],
    ) -> FakeTensor | None:
        from torch._higher_order_ops.utils import registered_hop_fake_fns

        flat_args, args_spec = pytree.tree_flatten((args, kwargs))

        # DO NOT PUT LOGIC BEFORE UNRECOGNIZED TYPE CHECKING
        # We must throw NotImplemented in case of unrecognized types to handle subclasses.
        # Throwing the exception will pass the control to the next __torch_dispatch__.
        # See [subclass inputs] below
        # NB: If you're seeing a mysterious infinite loop involving fake
        # tensor, it might be related to this line.  Though I'm not sure
        # how you'll know to read this comment, as this line won't show up
        # in the stack trace.
        has_unrecognized_types = _check_for_subclass(flat_args)
        if has_unrecognized_types:
            unrecognized_types = [
                type(x) for x in flat_args if _check_for_subclass_arg(x)
            ]
            not_implemented_log.debug(
                "FakeTensorMode unrecognized subclass(es): %s", unrecognized_types
            )
            return NotImplemented

        flat_arg_fake_tensors = [t for t in flat_args if self.is_our_fake(t)]
        has_symbolic_sizes = any(
            i._has_symbolic_sizes_strides for i in flat_arg_fake_tensors
        ) or any(isinstance(a, SymInt) for a in flat_args)

        converter = self.fake_tensor_converter

        is_lift_func = func in self.lift_fns

        # If we are trying to avoid device init, then we need to avoid constant
        # prop on constant tensors for ops that change devices.
        avoiding_device_init = False
        if self.avoid_device_init:
            if (
                func is torch.ops.aten._to_copy.default
                and "device" in kwargs
                and kwargs["device"].type != "cpu"  # type: ignore[attr-defined]
            ):
                avoiding_device_init = True
            if func is torch.ops.prims.device_put.default:
                avoiding_device_init = True

        # skip const prop for aten._to_copy if
        # 1. input tensor is on "meta" device
        # 2. destination device is unavailable, captured by `avoiding_device_init`
        device_conversion_skip_const_prop = (
            func is torch.ops.aten._to_copy.default
            and isinstance(args[0], torch.Tensor)
            and args[0].device.type == "meta"
        ) or avoiding_device_init

        # To constant propagate through these functions:
        # 1, If this is a lift due to a torch.tensor call,
        #    the input tensor is guaranteed to be a
        #    constant, so we keep a copy of the original argument along so
        #    we can query it if we're asked to item() it at some later point.
        #    (Note that you can always call a lift fn manually, so we do
        #    have to check if there are any fake tensors!)
        # 2, Some functions that allow Python numbers to bind to Tensors, e.g, torch.div
        if (is_lift_func and not flat_arg_fake_tensors) or (
            should_allow_numbers_as_tensors(func)
            and not has_symbolic_sizes
            and not flat_arg_fake_tensors
            and not device_conversion_skip_const_prop
        ):
            if not all(t.constant is not None for t in flat_arg_fake_tensors):
                raise AssertionError(
                    f"{func} should not have fake inputs without constants"
                )
            const_flat_args = [
                a.constant if self.is_our_fake(a) else a for a in flat_args
            ]
            const_args, const_kwargs = pytree.tree_unflatten(const_flat_args, args_spec)
            out = func(*const_args, **const_kwargs)
            if type(out) is Tensor and self.may_turn_const(out):
                # NB: not in_kernel_invocation_manager because we're doing real
                # compute here
                # NB: no_dispatch() here is VERY DANGEROUS (like, segfault
                # dangerous) if this is actually a wrapper subclass tensor,
                # therefore the exact type test above
                with no_dispatch():
                    out = out.clone()
                return converter.from_real_tensor(self, out, make_constant=True)

        # if we are in the dispatch mode, we will enter this function even if the inputs
        # are not FakeTensors. For now, throw if any non-Fake Tensor inputs
        # and just support constructors.

        # this is generated from torch.tensor(), which does not use the
        # dispatcher, to allow wrapper subclasses to wrap the new tensor
        if is_lift_func:
            if len(kwargs) != 0 or len(args) != 1:
                raise AssertionError(
                    f"Expected exactly one arg for lift func, got args={args} kwargs={kwargs}"
                )

            if type(args[0]) is Tensor:
                return converter.from_real_tensor(self, args[0])

        # Recompute flat_arg_fake_tensors here again in case some of the inputs
        # were real tensors and fakified in validate_and_convert_non_fake_tensors
        (flat_args, flat_arg_fake_tensors) = self.validate_and_convert_non_fake_tensors(
            func, converter, flat_args, args_spec
        )
        del args, kwargs  # Invalidated

        # The current constant handling only support tracing systems
        # (aot autograd, torchdynamo) where each operation is run consecutively.
        # Because each operation is run in order, we can trace out and support
        # sequences like: x = torch.tensor(0.); y = x.add_(1)
        # Whenever a constant is written to but with inputs that cannot be evaluated
        # statically, such as random_(), we invalidate all constants that alias the input
        # We will rely on functionalization for use of fake tensors constants as persistent
        # objects on an FX Graph.

        all_constant = all(e.constant is not None for e in flat_arg_fake_tensors)
        if (
            isinstance(func, torch._ops.OpOverload)
            and torch.Tag.nondeterministic_seeded not in func.tags
            # We dispatch size/stride/numel on the FakeTensor not its constant, so bail on inplace_view.
            # Example: fake_a.transpose_(0,1) would mutate fake_a.constant in-place, changing its
            # shape from (2,3) to (3,2), while fake_a.shape still reports (2,3) → divergence.
            # However, detach_ is safe: it only mutates requires_grad (not shape/stride/data),
            # and constants are used purely for their values, not autograd.
            and (
                torch.Tag.inplace_view not in func.tags or func is aten.detach_.default
            )
            and all_constant
            and len(flat_arg_fake_tensors) != 0
            and not has_symbolic_sizes
            and not avoiding_device_init
            and func is not aten._nested_tensor_from_tensor_list.default
        ):
            const_flat_args = [
                a.constant if self.is_our_fake(a) else a for a in flat_args
            ]
            const_args, const_kwargs = pytree.tree_unflatten(const_flat_args, args_spec)

            # NB: not in_kernel_invocation_manager(self) as we want to do REAL
            # compute
            with no_dispatch():
                out = func(*const_args, **const_kwargs)

            flat_out = pytree.tree_leaves(out)
            flat_out_tensors = [t for t in flat_out if isinstance(t, Tensor)]
            all_constant = all(self.may_turn_const(t) for t in flat_out_tensors)

            if all_constant:
                return pytree.tree_map_only(
                    Tensor,
                    lambda t: converter.from_real_tensor(self, t, make_constant=True),
                    out,
                )

            # we weren't able to turn outputs to constants,
            # so invalidate all constants that might be aliases of the outputs
            for ten in flat_out_tensors:
                converter.invalidate_constant_aliases(ten)

        # we are falling through to running non constant tensors, any input constant that
        # is written to must be invalidated
        args, kwargs = pytree.tree_unflatten(flat_args, args_spec)

        if (
            isinstance(func, torch._ops.HigherOrderOperator)
            and func in registered_hop_fake_fns
        ):
            # Reenable the fake tensor mode for the registered fake function
            maybe_ignore_fresh_unbacked_symbols = (
                contextlib.nullcontext
                if self.shape_env is None
                else self.shape_env.ignore_fresh_unbacked_symbols
            )

            with self, maybe_ignore_fresh_unbacked_symbols():
                return registered_hop_fake_fns[func](*args, **kwargs)

        self.invalidate_written_to_constants(func, flat_arg_fake_tensors, args, kwargs)

        def maybe_to_real_tensor(
            t: T,
        ) -> T | Tensor | torch._C.ScriptObject | None:
            if isinstance(t, FakeTensor):
                return t.real_tensor
            elif isinstance(t, py_sym_types):
                if self.shape_env is None:
                    raise AssertionError(
                        "self.shape_env must not be None for symbolic types"
                    )
                return t.node.pytype(
                    t.node.expr.xreplace(self.shape_env.backed_var_to_val).xreplace(
                        self.shape_env.real_tensor_prop_unbacked_vals
                    )
                )
            elif isinstance(t, FakeScriptObject):
                return t.real_obj
            else:
                return t

        from torch.fx.experimental.symbolic_shapes import (
            compute_unbacked_bindings,
            free_unbacked_symbols,
        )

        nil = object()

        real_out = nil
        if (
            self.propagate_real_tensors
            and all(e.real_tensor is not None for e in flat_arg_fake_tensors)
            and not any(
                (
                    isinstance(a, py_sym_types)
                    and (syms := free_unbacked_symbols(a))
                    and self.shape_env is not None
                    and any(
                        s not in self.shape_env.real_tensor_prop_unbacked_vals
                        for s in syms
                    )
                )
                for a in flat_args
            )
        ):
            log.debug("propagate_real_tensors %s", func)
            real_flat_args = [maybe_to_real_tensor(a) for a in flat_args]
            real_args, real_kwargs = pytree.tree_unflatten(real_flat_args, args_spec)

            is_builtin = library_utils.is_builtin(func)
            if not is_builtin:
                mutation_checker = library_utils.MutationChecker(
                    func, real_flat_args, args_spec
                )

            try:
                real_out = func(*real_args, **real_kwargs)
            except ZeroDivisionError as exc:
                # we shouldn't broadly catch all errors here;
                # some come from real-kernel mutation/aliasing checks we want to run.
                # add more exception types as needed.
                log.debug(
                    "real-tensor fallback failed for %s: %s; silently ignoring",
                    func,
                    exc,
                )

            if not is_builtin:
                mutation_checker.check()  # type: ignore[possibly-undefined]
                library_utils.check_aliasing_constraint(func._name, flat_args, real_out)

        elif self.propagate_real_tensors:
            # This can happen occasionally legitimately, specifically when you
            # are inside the meta of a data dependent operation and you create
            # a tensor on an unbacked SymInt; at this point in time we don't
            # know what the unbacked SymInt is, but we will know later.
            # However, if there's a bug in the condition above, this condition
            # will also trigger.
            log.debug(
                "SKIPPED propagate_real_tensors %s(%s, %s) %s",
                func,
                flat_arg_fake_tensors,
                flat_args,
                self.shape_env.real_tensor_prop_unbacked_vals
                if self.shape_env
                else None,
            )

        def maybe_propagate_real_tensors(fake_out: T) -> T:
            import sympy

            log.debug("maybe_propagate_real_tensors %s", func)

            def go(t: object, real_t: Tensor) -> None:
                if isinstance(t, FakeTensor):
                    # NB: unconditionally overwrite
                    log.debug(
                        "maybe_propagate_real_tensors %s -> %s", id(t), id(real_t)
                    )
                    t.real_tensor = real_t
                    for s, real_s in zip(t.size(), real_t.size()):
                        go(s, real_s)  # type: ignore[arg-type]
                    for s, real_s in zip(t.stride(), real_t.stride()):
                        go(s, real_s)  # type: ignore[arg-type]
                    go(t.storage_offset(), real_t.storage_offset())  # type: ignore[arg-type]
                elif isinstance(t, py_sym_types) and free_unbacked_symbols(t):
                    if isinstance(t.node.expr, sympy.Symbol):
                        if self.shape_env is None:
                            raise AssertionError(
                                "self.shape_env must not be None for symbolic Symbol"
                            )
                        self.shape_env.set_real_tensor_prop_unbacked_vals(
                            t.node.expr, real_t
                        )
                    elif (
                        isinstance(s := t.node.expr, sympy.Eq)
                        and isinstance(s.lhs, sympy.Symbol)
                        and s.rhs == 1
                    ):
                        if self.shape_env is None:
                            raise AssertionError(
                                "self.shape_env must not be None for symbolic Eq"
                            )

                        self.shape_env.set_real_tensor_prop_unbacked_vals(s, real_t)

            if real_out is not nil:
                # cross check fake/real outputs, and optionally override fake kernel mismatches
                if not torch._functorch.config.generate_fake_kernels_from_real_mismatches:
                    self._maybe_infer_fake_kernel_from_pytree_out(
                        func,
                        (args, kwargs),
                        (real_args, real_kwargs),
                        fake_out,
                        real_out,
                    )
                else:
                    # this can override the output only when the flag is True
                    fake_out = self._maybe_infer_fake_kernel_from_pytree_out(  # type: ignore[assignment]
                        func,
                        (args, kwargs),
                        (real_args, real_kwargs),
                        fake_out,
                        real_out,
                    )

                # populate real_tensor_prop_unbacked_vals
                if (
                    not isinstance(fake_out, Tensor)
                    and not isinstance(real_out, Tensor)
                    and type(fake_out) is not type(real_out)
                ):
                    # This can happen when decompositions have different return types,
                    # e.g. namedtuple vs. tuple vs. list.
                    tree_map_(
                        go,
                        tuple(pytree.tree_flatten(fake_out)),
                        tuple(pytree.tree_flatten(real_out)),
                    )
                else:
                    tree_map_(go, fake_out, real_out)

                # If a data-dependent op is used in a decomposition, we
                # may need to get the unbacked settings "early"
                # TODO: Is this really needed?
                compute_unbacked_bindings(self.shape_env, fake_out, peek=True)

            return fake_out

        # Try for fastpath
        if has_symbolic_sizes:
            fast_impl = get_fast_op_impls().get(func)
            if fast_impl is not None:
                return maybe_propagate_real_tensors(fast_impl(self, *args, **kwargs))

        # If there's a Python meta, prefer that over the decomposition
        from torch._decomp import meta_table

        if (
            func not in meta_table
            and not self.cpp_meta_supports_symint(func)
            and not (
                has_symbolic_sizes and func in self._unbacked_special_fake_handling_ops
            )
        ):
            from torch._decomp import decomposition_table

            # Prefer Python decompositions over C++ ones
            if func in decomposition_table and (
                has_symbolic_sizes
                or (
                    # TODO: Remove these exclusions, so that we can remove
                    # this leg entirely
                    torch_decomp_decompositions(func)
                    and all(not is_sparse_any(e) for e in flat_arg_fake_tensors)
                )
            ):
                with self:
                    return maybe_propagate_real_tensors(
                        decomposition_table[func](*args, **kwargs)
                    )

            with self:
                # Decomposes CompositeImplicitAutograd ops
                r = func.decompose(*args, **kwargs)
                if r is not NotImplemented:
                    return maybe_propagate_real_tensors(r)

        # prims already wrap FakeTensor inputs to FakeTensor outputs
        # and do device logic, we dont need do anything but run them
        # and ensure that Meta kernels are dispatched to (see)
        # Fake Tensor Dispatch Keys
        # TODO - we should be use the prim aten impl
        # TODO - fix prims complex ops
        if (
            "prims::" in func._schema.name
            and hasattr(func, "prim_meta_impl")
            and not stride_incorrect_op(func)
        ):
            with self:
                return maybe_propagate_real_tensors(
                    func.prim_meta_impl(*args, **kwargs)
                )

        profiles = torch._dynamo.config._custom_ops_profile
        if profiles is not None:
            if func in profiles.data:
                return profiles.generic_fake_kernel(func, self, *args, **kwargs)

        if (
            self.propagate_real_tensors
            and real_out is not nil
            and not library_utils.is_builtin(func)
            and self.shape_env is not None
        ):
            # Automatically infer a Fake kernel if there isn't one.
            if not library_utils.has_fake_kernel(func):
                result = inferred_fake_kernel_from_real_out(self, func, real_out)

                dtrace_structured(
                    "missing_fake_kernel",
                    metadata_fn=lambda: {
                        "op": str(func),
                    },
                )
                return maybe_propagate_real_tensors(result)

        # Users can register FakeTensor rules for custom operators
        # Call them if they exist.
        maybe_fake_impl = torch._library.simple_registry.singleton.find(
            func.name()
        ).fake_impl.kernel
        if maybe_fake_impl:
            try:
                ctx = torch._library.fake_impl.FakeImplCtx(self, func)
                with torch._library.fake_impl.set_ctx_getter(lambda: ctx), self:
                    result = maybe_fake_impl(*args, **kwargs)
                    return maybe_propagate_real_tensors(result)

            except MissingOpProfile as e:
                # If we have a fake kernel registered generated from OpProfiles
                # but there doesn't exist a profile for the existing inputs, and we are in
                if (
                    self.propagate_real_tensors
                    and real_out is not nil
                    and not library_utils.is_builtin(func)
                    and self.shape_env is not None
                ):
                    result = inferred_fake_kernel_from_real_out(self, func, real_out)

                    dtrace_structured(
                        "missing_fake_kernel",
                        metadata_fn=lambda: {
                            "op": str(func),
                        },
                    )
                    return maybe_propagate_real_tensors(result)
                else:
                    raise e

        # special handling for funcs registered through `register_op_impl`,
        # e.g., manipulating args on constructor calls to construct meta tensors
        # and then afterwards wrapping them to a FakeTensor
        for run_impl_check, op_impl in op_implementations_checks:
            if run_impl_check(func):
                # pyrefly: ignore [bad-argument-count]
                op_impl_out = op_impl(self, func, *args, **kwargs)
                if op_impl_out is not NotImplemented:
                    # pyrefly: ignore [bad-return]
                    return maybe_propagate_real_tensors(op_impl_out)

        def maybe_run_unsafe_fallback(
            error: RuntimeError | None = None,
        ) -> FakeTensor | None:
            # We infer the meta of custom ops that return None to just
            # return None, and Tag.out ops to return their out= args.
            # Custom ops are not allowed to mutate metadata of their
            # inputs, so this is safe.
            if torch._library.utils.can_generate_trivial_fake_impl(func):
                return torch._library.utils.generate_trivial_fake_impl(
                    func, *args, **kwargs
                )
            # no meta kernel registered, fallback to kernel for the device
            if has_symbolic_sizes or not self.can_run_unsafe_fallback(func):
                raise UnsupportedOperatorException(func)
            if error is None:
                error = UnsupportedOperatorException(func)
            return run_fallback_kernel(self, func, flat_args, args_spec, error)

        # Optimization: If there is no Meta kernel, it takes a surprisingly long
        # amount of time to catch the NotImplementedError, so we check it here.
        if not has_meta(func):
            fallback = maybe_run_unsafe_fallback()
            return maybe_propagate_real_tensors(fallback)

        # run kernel registered to meta for func, which include
        # python meta registrations, prims, decomps, and c++ meta fns (structured kernels)
        # It's possible that the kernel will return NotImplementedError
        try:
            with in_kernel_invocation_manager(self):
                r = func(*args, **kwargs)
        except NotImplementedError as not_implemented_error:
            return maybe_run_unsafe_fallback(not_implemented_error)
        except Exception:
            log.exception("failed while attempting to run meta for %s", func)
            raise

        return maybe_propagate_real_tensors(
            self.wrap_meta_outputs_with_default_device_logic(
                r, func, flat_args, device=kwargs.get("device")
            )
        )