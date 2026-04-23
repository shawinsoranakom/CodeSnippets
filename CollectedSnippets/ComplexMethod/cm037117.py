def cls_decorator_helper(cls: type[_T]) -> type[_T]:
        # helper to pass `dynamic_arg_dims` to `_support_torch_compile`
        # to avoid too much indentation for `_support_torch_compile`
        if not hasattr(cls, "forward"):
            raise TypeError("decorated class should have a forward method.")
        sig = inspect.signature(cls.forward)
        inferred_dynamic_arg_dims = dynamic_arg_dims
        if inferred_dynamic_arg_dims is None:
            inferred_dynamic_arg_dims = {}
            for k, v in sig.parameters.items():
                if v.annotation in [
                    torch.Tensor,
                    torch.Tensor | None,
                    torch.FloatTensor,
                    torch.FloatTensor | None,
                    IntermediateTensors,
                    IntermediateTensors | None,
                ]:
                    inferred_dynamic_arg_dims[k] = 0

            logger.debug(
                ("Inferred dynamic dimensions for forward method of %s: %s"),
                cls,
                list(inferred_dynamic_arg_dims.keys()),
            )

        if len(inferred_dynamic_arg_dims) == 0:
            raise ValueError(
                "No dynamic dimensions found in the forward method of "
                f"{cls}. Please provide dynamic_arg_dims explicitly."
            )

        for k in inferred_dynamic_arg_dims:
            if k not in sig.parameters:
                raise ValueError(
                    f"Argument {k} not found in the forward method of {cls}"
                )
        return _support_torch_compile(
            cls,
            inferred_dynamic_arg_dims,
            mark_unbacked_dims,
            enable_if,
            is_encoder,
            shape_invariants,
        )