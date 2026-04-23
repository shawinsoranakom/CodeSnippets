def try_propagate(
        self,
        mesh: DeviceMesh,
        input_placements: tuple[tuple[Placement, ...], ...],
        input_specs: list[DTensorSpec],
    ) -> OpStrategy | None:
        """Try to match input placements against single-dim strategy rules on every mesh dim.

        Checks whether the given input placements independently match a rule in
        strategy_lookup on each mesh dimension, and that all inputs are shardable
        with those placements. If so, returns an OpStrategy with the matched output
        placements and zero redistribute costs.
        """
        from torch.distributed.tensor._ops.utils import is_tensor_shardable

        selected_output_placements: list[tuple[Placement | None, ...]] = []
        for mesh_dim in range(mesh.ndim):
            input_placements_for_dim = tuple(
                placements[mesh_dim] for placements in input_placements
            )
            output_for_dim = self.strategy_lookup.get(input_placements_for_dim)
            if output_for_dim is not None:
                selected_output_placements.append(output_for_dim)
            else:
                return None

        arg_specs = [
            DTensorSpec(mesh, placements, tensor_meta=input_spec.tensor_meta)
            for placements, input_spec in zip(input_placements, input_specs)
        ]
        if not all(
            is_tensor_shardable(
                spec.tensor_meta.shape,
                spec,
                allow_unbacked_sharding=self.allow_unbacked_sharding,
            )
            or (self.allow_uneven_sharding and input_spec.placements == spec.placements)
            for spec, input_spec in zip(arg_specs, input_specs)
            if spec.tensor_meta is not None
        ):
            return None

        output_spec = (
            _build_output_specs(
                mesh,
                selected_output_placements,
                self.num_outputs,
                self.output_metas,
            )
            if self.num_outputs > 0
            else None
        )
        return OpStrategy(
            [
                OpSpec(
                    output_specs=output_spec,
                    input_specs=arg_specs,
                    redistribute_cost=[[0.0] for _ in input_specs],
                )
            ]
        )