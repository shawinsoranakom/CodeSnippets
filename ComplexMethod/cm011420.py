def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        args_schema, kwargs_schema = tree_map(
            lambda x: getattr(x, "_spec", x) if isinstance(x, torch.Tensor) else x,
            (args, kwargs or {}),
        )

        if not tree_any(
            lambda x: isinstance(x, DTensorSpec), (args_schema, kwargs_schema)
        ):
            raise NotImplementedError(f"No DTensorSpec found in args/kwargs for {func}")

        # Set schema_info so the LRU cache key includes static args
        op_schema = OpSchema(func, args_schema, kwargs_schema)
        schema_info = self.sharding_prop.op_to_schema_info.get(func)
        if schema_info is None:
            schema_info = (
                self.sharding_prop.op_to_schema_info_for_single_dim_strategy.get(func)
            )
        if schema_info is not None:
            op_schema.schema_info = schema_info
            op_schema._recompute_comparison_key()

        if _are_we_tracing():
            output_sharding = self.sharding_prop.propagate_op_sharding_non_cached(
                op_schema
            )
        else:
            output_sharding = self.sharding_prop.propagate_op_sharding(op_schema)

        if (
            output_sharding.needs_redistribute  # pyrefly: ignore [missing-attribute]
            and (
                redistribute_schema
                := output_sharding.redistribute_schema  # pyrefly: ignore [missing-attribute]
            )
            is not None
        ):
            # a pure .needs_redistribute check is too broad; we want to ban redistribution,
            # but this flag is set for view ops that convert global shape -> local shape args.
            # During decomposition tracing on meta tensors at global shape, the shape adjustment
            # is irrelevant — only reject true redistribution.
            for orig, desired in zip(
                op_schema.args_spec,
                redistribute_schema.args_spec,  # pyrefly: ignore [missing-attribute]
            ):
                if orig.placements != desired.placements:
                    raise RuntimeError(
                        f"Decomposition requires redistribution for {func}"
                    )

        out = func(*args, **kwargs)
        # pyrefly: ignore [missing-attribute]
        self._record_output_specs(out, output_sharding.output_spec)
        return out