def _handle_insert_op_in_graph(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker | None:
        from .builder import wrap_fx_proxy, wrap_fx_proxy_cls

        if kwargs and not self.tensor_args(*args, *kwargs.values()):
            return None

        # insert handling for torch function here
        from .builder import SourcelessBuilder
        from .torch_function import can_dispatch_torch_function, dispatch_torch_function

        global BUILTIN_TO_TENSOR_RFN_MAP, BUILTIN_TO_TENSOR_FN_MAP
        if can_dispatch_torch_function(tx, args, kwargs):
            # Only remap the fn to tensor methods if we aren't exporting
            # export serde does not handle method descriptors today
            if not tx.export:
                # Ensure the builtin maps are populated before accessing them
                populate_builtin_to_tensor_fn_map()
                # Use sourceless builder, we built the map ourselves
                if not args[0].is_tensor():
                    if self.fn in BUILTIN_TO_TENSOR_RFN_MAP:
                        func = BUILTIN_TO_TENSOR_RFN_MAP[self.fn]
                    else:
                        func = BUILTIN_TO_TENSOR_FN_MAP[self.fn]

                    tmp = args[0]
                    # swap args and call reverse version of func
                    args[0] = args[1]  # type: ignore[index]
                    args[1] = tmp  # type: ignore[index]
                else:
                    func = BUILTIN_TO_TENSOR_FN_MAP[self.fn]
            else:
                func = self.fn

            fn_var = SourcelessBuilder.create(tx, func)

            return dispatch_torch_function(tx, fn_var, args, kwargs)

        fn = self.fn
        try:
            # Constant fold for constant tensor and python constants
            if self.python_and_tensor_constant_only(*args, **kwargs):
                from ..bytecode_transformation import unique_id
                from .functions import invoke_and_store_as_constant

                return invoke_and_store_as_constant(
                    tx, fn, unique_id(fn.__name__), args, kwargs
                )

            if fn in IN_PLACE_DESUGARING_MAP and isinstance(
                args[0], variables.ConstantVariable
            ):
                # In-place operators like += usually mustate tensor
                # values, but in the edge case of immutable values they
                # re-bind the variable.
                #
                # The easiest way to keep the graph consistent in this
                # scenario is to de-sugar eagerly.
                fn = IN_PLACE_DESUGARING_MAP[fn]
                args = [args[0], args[1]]  # type: ignore[assignment]

            if fn is operator.getitem and isinstance(args[1], SymNodeVariable):
                # Standard indexing will force specialization due to
                # __index__.  Rewrite as a regular torch op which will
                # trace fine
                fn = torch.select
                args = [
                    args[0],
                    variables.VariableTracker.build(tx, 0),
                    args[1],
                ]  # type: ignore[assignment]

            # Interaction between ndarray and tensors:
            #   We prefer the tensor op whenever there are tensors involved
            # NB: Use exact type check here - NumpyNdarrayVariable is a TensorVariable
            # subclass but should NOT trigger the tensor path
            if check_numpy_ndarray_args(args, kwargs) and not any(
                type(arg) is TensorVariable for arg in args
            ):
                proxy = tx.output.create_proxy(
                    "call_function",
                    numpy_operator_wrapper(fn),
                    *proxy_args_kwargs(args, kwargs),
                )

                return wrap_fx_proxy_cls(variables.NumpyNdarrayVariable, tx, proxy)

            if fn is operator.eq and len(args) == 2 and args[0].is_tensor():
                # Dynamo expects `__eq__` str while operator.eq gives just `eq`
                # TODO - supporting all comparison operators could also work but
                # it fails lots of tests because graph str changes.
                return args[0].call_method(tx, "__eq__", list(args[1:]), kwargs)
            proxy = tx.output.create_proxy(
                "call_function",
                fn,
                *proxy_args_kwargs(args, kwargs),
            )
            if any(isinstance(arg, FakeItemVariable) for arg in args):
                return wrap_fx_proxy_cls(
                    FakeItemVariable,
                    tx,
                    proxy,
                )
            elif check_unspec_python_args(args, kwargs):
                _args, _kwargs = self.unwrap_unspec_args_kwargs(args, kwargs)
                raw_value = fn(*_args, **_kwargs)

                need_unwrap = any(
                    x.need_unwrap
                    for x in itertools.chain(args, kwargs.values())
                    if isinstance(x, variables.UnspecializedPythonVariable)
                )

                return wrap_fx_proxy_cls(
                    UnspecializedPythonVariable,
                    tx,
                    proxy,
                    raw_value=raw_value,
                    need_unwrap=need_unwrap,
                )
            elif all(isinstance(x, SymNodeVariable) for x in args):
                return SymNodeVariable.create(tx, proxy, None)
            else:
                # Work around for vision_maskrcnn due to precision difference
                # specialize the dividend when float divide by tensor
                if fn is operator.truediv and isinstance(
                    args[0], variables.UnspecializedPythonVariable
                ):
                    args = list(args)
                    args[0] = args[0].as_python_constant()
                return wrap_fx_proxy(tx, proxy)

        except NotImplementedError:
            unimplemented(
                gb_type="unimplemented builtin op on tensor arguments",
                context=f"partial tensor op: {self} {args} {kwargs}",
                explanation=f"Dynamo does not know how to trace builtin operator {self.fn} with tensor arguments",
                hints=[*graph_break_hints.SUPPORTABLE],
            )