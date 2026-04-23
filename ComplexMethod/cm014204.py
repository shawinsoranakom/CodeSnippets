def method_type(
        self,
        tx: "InstructionTranslator",
        dtype: Any | None = None,
        non_blocking: bool = False,
        **kwargs: Any,
    ) -> VariableTracker | None:
        if (
            dtype is None
            and self.dtype is not None
            and isinstance(self.device, torch.device)
        ):
            tensortype = next(
                k for k, v in tensortype_to_dtype.items() if self.dtype in v
            )
            if self.device.type == "cpu":
                return VariableTracker.build(tx, f"torch.{tensortype.__name__}")
            else:
                return VariableTracker.build(
                    tx, f"torch.{self.device.type}.{tensortype.__name__}"
                )
        elif (
            dtype is not None
            and fqn(type(dtype.as_python_constant())) == "torch.tensortype"
        ):
            # torch.FloatTensor, etc. are all of type "torch.tensortype".
            # torch.fx's tracer fails on these types, because it doesn't support arguments of torch.tensortype type.
            # So, we pass it in as a string (which is also supported, see above implementation for .type() with 0 args)
            tensor_type = dtype.as_python_constant()
            tensor_type_const = VariableTracker.build(tx, fqn(tensor_type))

            from .builder import wrap_fx_proxy

            if non_blocking:
                kwargs = {"non_blocking": non_blocking, **kwargs}

            return wrap_fx_proxy(
                tx,
                tx.output.create_proxy(
                    "call_method",
                    "type",
                    *proxy_args_kwargs([self, tensor_type_const], kwargs),
                ),
            )
        return None