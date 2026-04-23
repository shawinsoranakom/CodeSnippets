def _default(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        bounds = self._bound_variable(name, *args, **kwargs)

        value = getattr(self.parent_handler, name)(*args, **kwargs)
        dtype_handler = DtypePropagationOpsHandler()
        shape_handler = ShapePropagationOpsHandler()

        backend = get_current_backend()

        shape_op = getattr(shape_handler, name)
        output_dtype = None
        output_shape = None

        if name == "masked" and backend == "triton":
            output_dtype = value.dtype
            output_shape = value.shape
        elif name == "masked" and backend == "cpp":
            output_dtype = V.interpreter.current_node.meta.get(
                OptimizationContext.key, None
            ).dtype
            # TODO: fix me
            output_shape = None
        elif backend in ("triton", "cpp", "mps"):
            dtype_op = getattr(dtype_handler, name)
            output_dtype = dtype_op(*args, **kwargs)
            output_shape = shape_op(*args, **kwargs)

        if backend in ("triton", "cpp"):
            # maybe there are some exceptions on mps?
            assert output_dtype is not None

        output_idx = 0

        def do_cse(v: str | CSEVariable) -> CSEVariable:
            # we tree_map over the output, so we need to fetch corresponding dtype
            nonlocal output_idx
            var_dtype: torch.dtype | None = (
                output_dtype[output_idx]
                if isinstance(output_dtype, (list, tuple))
                else output_dtype
            )
            var_shape: BlockShapeType = (
                output_shape[output_idx]  # type: ignore[assignment]
                if isinstance(output_shape, (list, tuple))
                and len(output_shape) > 0
                and isinstance(output_shape[0], (list, tuple))
                else output_shape
            )
            output_idx += 1

            # some cpp op implementations don't set the dtype
            if isinstance(v, CSEVariable):
                if backend == "cpp" and v.dtype is None:
                    v.dtype = var_dtype
                if v.shape is None:
                    v.shape = var_shape

            csevar = V.kernel.cse.generate(
                V.kernel.compute,
                v,
                bounds=bounds,
                dtype=output_dtype,
                shape=output_shape,
            )

            csevar.update_on_args(name, args, kwargs)

            if (
                config.test_configs.runtime_triton_dtype_assert
                or config.test_configs.static_cpp_dtype_assert
            ):
                assert var_dtype is not None
                check_dtype(V.kernel.compute, csevar, var_dtype)

            if config.test_configs.runtime_triton_shape_assert:
                assert output_shape is not None
                check_shape(V.kernel.compute, csevar, output_shape)

            if config.runtime_triton_nan_asserts:
                check_nan(V.kernel.compute, csevar)

            return csevar

        return pytree.tree_map(do_cse, value)