def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: "dict[str, VariableTracker]",
    ) -> "VariableTracker":
        from . import SymNodeVariable
        from .builder import wrap_fx_proxy

        if self.kind == AllowInGraphKind.NONSTRICT_TRACE:
            return self._call_nonstrict_traceable_function(tx, args, kwargs)

        if self.kind == AllowInGraphKind.LEAF_FUNCTION:
            return self._call_leaf_function(tx, args, kwargs)

        if self.torch_function_override_enabled(tx, args, kwargs):
            return dispatch_torch_function(tx, self, args, kwargs)

        if self.can_constant_fold_through() and check_unspec_or_constant_args(
            args, kwargs
        ):
            # constant fold functions need to be guarded.
            if self.value in constant_fold_functions_need_guards:
                assert self.source is not None
                source = CallFunctionNoArgsSource(self.source)
                install_guard(source.make_guard(GuardBuilder.EQUALS_MATCH))
            # constant fold
            try:
                return VariableTracker.build(
                    tx,
                    self.as_python_constant()(
                        *[x.as_python_constant() for x in args],
                        **{k: v.as_python_constant() for k, v in kwargs.items()},
                    ),
                )
            except (OverflowError, TypeError, ValueError) as exc:
                raise_observed_exception(
                    type(exc),
                    tx,
                    args=list(exc.args),
                )

        if self.is_tensor_method():
            name = self.value.__name__
            # Guard against inplace view op on input tensor (not supported)
            if args and args[0].is_tensor():
                tensor_var = args[0]
                # Check if input tensor and inplace_view op specifically
                if tensor_var.source is not None and hasattr(torch.ops.aten, name):
                    fn = getattr(torch.ops.aten, name)
                    if (
                        hasattr(fn, "overloads")
                        and hasattr(fn, fn.overloads()[0])
                        and torch.Tag.inplace_view
                        in getattr(fn, fn.overloads()[0]).tags
                    ):
                        unimplemented(
                            gb_type="Inplace op on input tensor",
                            context="",
                            explanation=f"Attempted to trace an inplace view op on input tensor {typestr(self.value)}.",
                            hints=[
                                *graph_break_hints.SUPPORTABLE,
                                "Ensure you do not modify input tensor in place.",
                            ],
                        )
            return self.call_tensor_method(tx, list(args), kwargs)

        special_handler = self._get_handlers().get(self.value)
        if special_handler:
            result = special_handler(self, tx, *args, **kwargs)
            if result:
                return result

        any_symints_or_symfloats = any(isinstance(x, SymNodeVariable) for x in args)

        all_ints_or_floats = all(
            isinstance(x, SymNodeVariable) or x.is_python_constant() for x in args
        )
        if (
            getattr(self.value, "__module__", "") == "torch"
            and self.value.__name__ in bin_ops
            and any_symints_or_symfloats
            and all_ints_or_floats
        ):
            msg = f"""\
Calling {str(self.value)} on only torch.SymInt arguments is not yet supported.
To support this behavior, we need to allow const-propping tensors that store symint data.
For now, dynamo will explicitly graph break when it encounters user code with this behavior.
"""
            log.warning(msg)
            unimplemented(
                gb_type="Attempted to call torch in-graph function on only torch.SymInt arguments",
                context=f"fn={self.value}, args={args}, kwargs={kwargs}",
                explanation=(
                    f"Attempted to call {str(self.value)} (that should be put in the FX graph) on only torch.SymInt arguments. "
                    "Dynamo does not support this."
                ),
                hints=[
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        # TODO(voz): Replace w/ dynamic shape rewrite table.
        # Ideally, we would be able to do this at ctor time, but alas we need a combination
        # of value + args to determine this.
        fn_ = self.value
        if any_symints_or_symfloats:
            torch_sym_op = f"_sym_{self.value.__name__}"
            if getattr(self.value, "__module__", None) == "math" and hasattr(
                torch, torch_sym_op
            ):
                fn_ = getattr(torch, torch_sym_op)

        # TODO for each of the following check on `out=` or `requires_grad=`
        # variant torch ops, the original function could come from a user
        # defined `@allow_in_graph` function as well, which doesn't have the
        # same semantics as the torch ops.

        # Calling fake tensor propagation can mutate the out= tensor in
        # tx.output.tracked_fakes. tracked_fakes are used to apply
        # symbolic_shape guards. Mutating them destroys the information
        # prior to tracing, which is essential for creating right
        # guards. So save the shape now, and check later if it has
        # changed. If it has, graph break.
        saved_out_shapes = None
        out_kwarg_vt = None
        if "out" in kwargs:
            out_kwarg_vt = kwargs["out"]

            # e.g., out=(t1, t2, ...)
            if isinstance(out_kwarg_vt, (TupleVariable, ListVariable)):
                saved_out_shapes = []
                for vt in out_kwarg_vt.items:
                    if vt.is_tensor():
                        shape = vt.as_proxy().node.meta["example_value"].shape
                    else:
                        shape = None
                    saved_out_shapes.append(shape)

            # e.g., out=output_tensor
            if out_kwarg_vt.is_tensor():
                saved_out_shapes = (
                    out_kwarg_vt.as_proxy().node.meta["example_value"].shape
                )

        # Ops that consume scalar values from tensors (via .item()) for computation only,
        # not for output shapes. When capture_scalar_outputs is enabled, these ops would
        # create unbacked symbols that are not in the outputs, causing
        # PendingUnbackedSymbolNotFound errors. We ignore these fresh unbacked symbols
        # since they only affect tensor values, not shapes.
        ops_consuming_unbacked_scalars = {
            # foreach ops with scalar/alpha arguments
            torch._foreach_add,
            torch._foreach_add_,
            torch._foreach_sub,
            torch._foreach_sub_,
            torch._foreach_mul,
            torch._foreach_mul_,
            torch._foreach_div,
            torch._foreach_div_,
            torch._foreach_clamp_max,
            torch._foreach_clamp_max_,
            torch._foreach_clamp_min,
            torch._foreach_clamp_min_,
            torch._foreach_maximum,
            torch._foreach_maximum_,
            torch._foreach_minimum,
            torch._foreach_minimum_,
            torch._foreach_pow,
            torch._foreach_pow_,
            torch._foreach_lerp,
            torch._foreach_lerp_,
            torch._foreach_addcmul,
            torch._foreach_addcmul_,
            torch._foreach_addcdiv,
            torch._foreach_addcdiv_,
        }
        ctx = nullcontext
        if fn_ in ops_consuming_unbacked_scalars:
            if tx.fake_mode and tx.fake_mode.shape_env:
                ctx = tx.fake_mode.shape_env.ignore_fresh_unbacked_symbols

        with ctx():
            tensor_variable = wrap_fx_proxy(
                tx=tx,
                proxy=tx.output.create_proxy(
                    "call_function",
                    fn_,
                    *proxy_args_kwargs(args, kwargs),
                ),
            )

        # Handle e.g., `torch.ones(10, requires_grad=True)`
        if (
            tensor_variable.is_tensor()
            and "requires_grad" in kwargs
            and kwargs["requires_grad"].as_python_constant()
        ):
            unimplemented(
                gb_type="Attempted to use tensor creation function with requires_grad=True",
                context=f"fn={self.value}, args={args}, kwargs={kwargs}",
                explanation="Dynamo does not support this.",
                hints=[
                    "Create the tensor outside the compiled region.",
                    "Do not set `requires_grad=True`.",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        # Handle e.g., `torch.add(a, b, out=result)`
        if saved_out_shapes is not None:
            # out variants of torch operators like torch.sort and torch.sigmoid
            # mutate the tensors in the out field.
            #
            # However, it's non-trivial to update all references of the old
            # `TensorVariable` to the new one returned (`result_var`), so we
            # take the conservative approach to graph break on size changes, and
            # assume other cases can fall through soundly.
            #
            # Note that although these tensor variables would hold different
            # proxies, the in-place mutation semantics is preserved in the FX
            # graph, so we won't have correctness issues.
            if isinstance(saved_out_shapes, list):
                for out_tensor_vt, saved_out_shape in zip(
                    out_kwarg_vt.items,  # type: ignore[union-attr]
                    saved_out_shapes,
                ):
                    if saved_out_shape is None:
                        # This should be extremely rare, but it's kept for now
                        # until we invest in enforcing the `out=` kwarg for only
                        # torch methods.
                        continue

                    assert out_tensor_vt.is_tensor()
                    fake_out = out_tensor_vt.proxy.node.meta["example_value"]
                    if saved_out_shape != fake_out.shape:
                        # It's hard to get out variants with resizing on graph inputs work
                        # properly across dynamo/aot/inductor, just fall back.
                        unimplemented(
                            gb_type="Shape mismatch with out= list of tensor variants",
                            context=f"fn={self.value}, args={args}, kwargs={kwargs}",
                            explanation=(
                                f"Shape mismatch when calling {self.value} with `out=`. "
                                f"Provided `out=` shape: {saved_out_shape}. Actual shape: {fake_out.shape}."
                            ),
                            hints=[
                                *graph_break_hints.SUPPORTABLE,
                            ],
                        )
                    if not torch._prims_common.is_contiguous(fake_out):
                        # It's difficult to handle strides correctly in functionalization
                        # when calling an out= op with a non-contiguous out argument
                        unimplemented(
                            gb_type="Attempted to call op with non-contiguous `out=` list of tensors",
                            context=f"self.value={self.value}, args={args}, kwargs={kwargs}",
                            explanation="Dynamo does not support this.",
                            hints=[
                                *graph_break_hints.SUPPORTABLE,
                            ],
                        )
            else:
                assert out_kwarg_vt is not None and out_kwarg_vt.is_tensor()
                assert "example_value" in out_kwarg_vt.as_proxy().node.meta
                fake_out = out_kwarg_vt.as_proxy().node.meta["example_value"]
                if saved_out_shapes != fake_out.shape:
                    # It's hard to get out variants with resizing on graph inputs work
                    # properly across dynamo/aot/inductor, just fall back.
                    unimplemented(
                        gb_type="Shape mismatch with out= tensor variant",
                        context=f"fn={self.value}, args={args}, kwargs={kwargs}",
                        explanation=(
                            f"Shape mismatch when calling {self.value} with `out=`. "
                            f"Provided `out=` shape: {saved_out_shapes}. Actual shape: {fake_out.shape}."
                        ),
                        hints=[
                            *graph_break_hints.SUPPORTABLE,
                        ],
                    )
                if not torch._prims_common.is_contiguous_or_false(fake_out):
                    # It's difficult to handle strides correctly in functionalization
                    # when calling an out= op with a non-contiguous out argument
                    unimplemented(
                        gb_type="Attempted to call op with non-contiguous `out=` tensor",
                        context=f"self.value={self.value}, args={args}, kwargs={kwargs}",
                        explanation="Dynamo does not support this.",
                        hints=[
                            *graph_break_hints.SUPPORTABLE,
                        ],
                    )

        return tensor_variable