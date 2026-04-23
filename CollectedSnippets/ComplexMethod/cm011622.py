def _fn(*args, **kwargs):
            bound = _fast_bind(sig, *args, **kwargs)
            type_promoting_args = tuple(
                bound.arguments[x]
                for x in self.type_promoting_arg_names  # type: ignore[union-attr]
                if x in bound.arguments
            )

            flattened_type_promoting_args = pytree.arg_tree_leaves(*type_promoting_args)
            compute_dtype, result_dtype = utils.elementwise_dtypes(
                *flattened_type_promoting_args,
                type_promotion_kind=self.type_promotion_kind,
            )

            promoted_args = {
                x: _maybe_convert_to_dtype(bound.arguments[x], compute_dtype)
                for x in self.type_promoting_arg_names  # type: ignore[union-attr]
                if x in bound.arguments
            }
            bound.arguments.update(promoted_args)

            result = fn(**bound.arguments)

            # Override the return_dtype if a dtype arg is present and not None
            if "dtype" in bound.arguments:
                maybe_dtype = bound.arguments["dtype"]
                if maybe_dtype:  # dtype cannot be None
                    result_dtype = maybe_dtype

            if isinstance(result, TensorLike):
                return _maybe_convert_to_dtype(result, result_dtype)
            if isinstance(result, Sequence):
                return tuple(_maybe_convert_to_dtype(x, result_dtype) for x in result)
            raise AssertionError(f"Unhandled result type: {type(result)}")