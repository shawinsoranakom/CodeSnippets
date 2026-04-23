def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from ..exc import unimplemented
        from ..utils import numpy_method_wrapper

        args, kwargs = self.patch_args(name, args, kwargs)

        if name == "astype":
            from .builtin import BuiltinVariable

            dtype_arg = None
            if "dtype" in kwargs:
                dtype_arg = kwargs["dtype"]
            elif len(args) > 0:
                dtype_arg = args[0]
            is_object_str = dtype_arg is not None and dtype_arg.is_constant_match("O")
            is_object_type = (
                isinstance(dtype_arg, BuiltinVariable) and dtype_arg.fn is object
            )
            if is_object_str or is_object_type:
                unimplemented(
                    gb_type="ndarray.astype(object)",
                    context=f"call_method {self} {name} {args} {kwargs}",
                    explanation=(
                        "`ndarray.astype('O')` or `ndarray.astype(object)` is not supported "
                        "by torch.compile, as there is no equivalent to object type in torch.Tensor. "
                        "This will be executed eagerly."
                    ),
                    hints=[*graph_break_hints.FUNDAMENTAL],
                )
        if name in ["__len__", "size", "tolist", "__iter__"]:
            # delegate back to TensorVariable
            return super().call_method(tx, name, args, kwargs)
        if name in ("tostring", "tobytes", "__delattr__"):
            unimplemented(
                gb_type="Unsupported ndarray method call",
                context=f"call_method {self} {name} {args} {kwargs}",
                explanation=f"`ndarray.{name}()` is not modelled in `torch._numpy`.",
                hints=[],
            )
        proxy = tx.output.create_proxy(
            "call_function",
            numpy_method_wrapper(name),
            *proxy_args_kwargs([self] + list(args), kwargs),
        )
        return NumpyNdarrayVariable.create(tx, proxy)