def invalidate_written_to_constants(
        self,
        func: OpOverload,
        flat_arg_fake_tensors: Sequence[FakeTensor],
        args: Sequence[object],
        kwargs: Mapping[str, object],
    ) -> None:
        any_constant = any(e.constant is not None for e in flat_arg_fake_tensors)
        schema_info = get_schema_info(func)
        if any_constant and schema_info.is_mutable():
            _, new_kwargs = normalize_function(  # type: ignore[misc]
                func,
                args=args,  # type: ignore[arg-type]
                kwargs=kwargs,  # type: ignore[arg-type]
                normalize_to_only_use_kwargs=True,
            )
            for k, v in new_kwargs.items():
                k = k if (k != "input" or schema_info.has_argument(k)) else "self"
                if (
                    self.is_our_fake(v)
                    and schema_info.is_mutable(k)
                    and v.constant is not None
                ):
                    self.fake_tensor_converter.invalidate_constant_aliases(v.constant)