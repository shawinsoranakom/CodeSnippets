def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if not config.trace_numpy:
            unimplemented(
                gb_type="attempted to trace numpy function with config.trace_numpy=False",
                context=f"numpy function: {self.value}, args: {args}, kwargs: {kwargs}",
                explanation=f"Attempted to trace numpy function {self.value} "
                "while `torch._dynamo.config.trace_numpy` was set to False.",
                hints=[
                    "Set `torch._dynamo.config.trace_numpy` to True to trace numpy functions.",
                ],
            )

        from ..utils import numpy_to_tensor_wrapper
        from .tensor import NumpyNdarrayVariable

        func = get_np_to_tnp_map().get(self.value)
        if func is None:
            unimplemented(
                gb_type="attempted to trace numpy function unsupported by PyTorch",
                context=f"numpy function: {self.value}, args: {args}, kwargs: {kwargs} (corresponding torch function: {func})",
                explanation=f"Can't find numpy numpy function {self.value} in torch._numpy.",
                hints=[
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        # We are dealing with a function that produces a const collection type (np.dtype, np.iinfo/np.finfo)
        assert func is not None
        if (
            collection_variable_typ := self.get_constant_collection_for_func(func)
        ) is not None:
            try:
                return collection_variable_typ(
                    self.value(
                        *[x.as_python_constant() for x in args],
                        **{k: v.as_python_constant() for k, v in kwargs.items()},
                    )
                )
            except AsPythonConstantNotImplementedError:
                unimplemented(
                    gb_type="numpy function that produces a const collection type encountered non-const arguments",
                    context=f"numpy function: {self.value}, args: {args}, kwargs: {kwargs} (corresponding torch function: {func})",
                    explanation=f"numpy function {self.value} that produces a const collection type "
                    "(e.g. np.dtype, np.iinfo/np.finfo) "
                    "received arguments that are not constant.",
                    hints=[
                        *graph_break_hints.USER_ERROR,
                    ],
                )
        else:
            if (
                func.__module__ == "torch._numpy.random"
                and config.use_numpy_random_stream
            ):
                unimplemented(
                    gb_type="attempted to trace torch._numpy.random function with config.use_numpy_random_stream=True",
                    context=f"numpy function: {self.value}, args: {args}, kwargs: {kwargs} (corresponding torch function: {func})",
                    explanation=f"Attempted to trace {self.value} when `torch._dynamo.config.use_numpy_random_stream` "
                    "is set to True.",
                    hints=[
                        "Set `torch._dynamo.config.use_numpy_random_stream` to False.",
                        f"Avoid calling {self.value}.",
                    ],
                )

            args, kwargs = NumpyNdarrayVariable.patch_args(func.__name__, args, kwargs)

            if self.can_constant_fold_through(func) and (
                check_unspec_or_constant_args(args, kwargs)
            ):
                # constant fold
                return VariableTracker.build(
                    tx,
                    self.as_python_constant()(
                        *[x.as_python_constant() for x in args],
                        **{k: v.as_python_constant() for k, v in kwargs.items()},
                    ),
                )

            # TODO Add all the functions that go from constants to constants to can_constant_fold_through
            proxy = tx.output.create_proxy(
                "call_function",
                numpy_to_tensor_wrapper(func),
                *proxy_args_kwargs(args, kwargs),
            )
            return NumpyNdarrayVariable.create(tx, proxy)