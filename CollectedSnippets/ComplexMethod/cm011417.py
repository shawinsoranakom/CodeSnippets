def _adjust_squeeze_to_global_singletons(self, schema: OpSchema) -> OpSchema | None:
        """
        Rewrite squeeze ops to squeeze.dims with only globally-singleton dims.
        Fixes bug where sharded dims with local size 1 get incorrectly squeezed.
        Returns None if no rewrite is needed (already squeeze.dims with correct args).
        """
        from torch.fx.experimental.symbolic_shapes import guard_or_false

        input_spec = cast(DTensorSpec, schema.args_schema[0])
        tensor_meta = input_spec.tensor_meta
        if tensor_meta is None:
            raise RuntimeError("squeeze requires tensor metadata")
        global_shape = tensor_meta.shape
        ndim = len(global_shape)

        def normalize(d: int) -> int:
            return d if d >= 0 else d + ndim

        def is_singleton(d: int) -> bool:
            nd = normalize(d)
            return 0 <= nd < ndim and guard_or_false(global_shape[nd] == 1)

        # guard_or_false: conservatively keep dims when size is symbolic/unknown
        if schema.op in (aten.squeeze.default, aten.squeeze_.default):
            target_dims = tuple(
                i for i, s in enumerate(global_shape) if guard_or_false(s == 1)
            )
        elif schema.op in (aten.squeeze.dim, aten.squeeze_.dim):
            dim = normalize(schema.args_schema[1])  # type: ignore[arg-type]
            target_dims = (dim,) if is_singleton(dim) else ()
        else:
            dims = cast(Sequence[int], schema.args_schema[1])
            target_dims = tuple(  # type: ignore[union-attr]
                normalize(d) for d in dims if is_singleton(d)
            )

        dims_variant = self.squeeze_op_to_dims_variant[schema.op]
        # Skip rewrite if already targeting the right op with the same dims
        if schema.op == dims_variant and len(schema.args_schema) > 1:
            existing_dims = schema.args_schema[1]
            if existing_dims == target_dims:
                return None
        return OpSchema(dims_variant, (input_spec, target_dims), {})