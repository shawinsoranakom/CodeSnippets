def propagate_strategy(
        self,
        op_schema: OpSchema,
    ) -> OpStrategy | None:
        if not tree_any(
            lambda x: isinstance(x, DTensorSpec),
            (op_schema.args_schema, op_schema.kwargs_schema),
        ):
            return None

        candidate_placements = self._get_candidate_placements(op_schema)
        mesh = try_find_mesh_from_args(
            op_schema.op,
            op_schema.args_schema + tuple(op_schema.kwargs_schema.values()),
        )

        fake_mesh = self._get_fake_mesh(mesh.device_type)
        single_dim_strategies = []
        output_placements: list[Placement | tuple[Placement, ...]] = []
        for input_placements in candidate_placements:
            try:
                output = self._propagate_through_decomp(
                    op_schema,
                    input_placements,
                    fake_mesh,
                )
            except NotImplementedError:
                return None
            except GuardOnDataDependentSymNode:
                return None
            except (RuntimeError, KeyError, IndexError):
                # TODO(pianpwk): RuntimeError is raised when redistribution is detected; switch to a custom error type
                # Runtime/KeyError/IndexError can also occur in view ops
                continue

            output_placements = (
                [output] if not isinstance(output, tuple) else list(output)
            )
            single_dim_strategies.append(output_placements + list(input_placements))

        if not single_dim_strategies:
            raise AssertionError(
                "Sharding propagation should have produced at least Replicate() strategy"
            )

        n_outputs = len(output_placements)
        strategy_schema = self.sharding_prop._wrap_with_op_strategy(op_schema)
        # Import here to avoid circular import at module load time
        from torch.distributed.tensor._ops.utils import expand_to_full_mesh_op_strategy

        return expand_to_full_mesh_op_strategy(
            mesh, strategy_schema, single_dim_strategies, input_index=n_outputs
        )