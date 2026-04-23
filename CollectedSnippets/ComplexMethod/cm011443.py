def generate_graph_based_transform_infos(
        self,
        src_spec: DTensorSpec,
        dst_spec: DTensorSpec,
        full_tensor_shape: tuple[int, ...],
    ) -> list[_TransformInfo]:
        # TODO(zpcore): Temporary workaround for backward compatibility where
        # _StridedShard was used to encode device shard order. We should migrate
        # to explicit `shard_order` instead.
        def _try_normalize_spec(
            spec: DTensorSpec,
        ) -> tuple[tuple[Placement, ...], ShardOrder]:
            if spec.use_strided_shard_as_shard_order:
                new_placements, shard_order = (
                    DTensorSpec._normalize_placements_into_shard_order(
                        spec.placements,
                        spec.mesh,
                        use_strided_shard_as_shard_order=True,
                    )
                )
                return new_placements, shard_order
            else:
                if spec.shard_order is None:
                    raise ValueError(f"Missing shard_order field in {spec}")
                return spec.placements, spec.shard_order

        src_placements, src_shard_order = _try_normalize_spec(src_spec)
        dst_placements, dst_shard_order = _try_normalize_spec(dst_spec)

        # In case _StridedShard still exists in placements, collect possible
        # split_factor values in the target placements. Need those values to
        # redistribute from Shard into _StridedShard.
        for placement in dst_placements:
            if isinstance(placement, _StridedShard):
                self.strided_shard_placements_in_target.add(placement)

        # Collect Partial reduce ops from src and dst placements. These are used
        # to generate R->P transitions only for reduce ops that are actually
        # present in the redistribution, avoiding unnecessary graph expansion.
        for placement in itertools.chain(src_placements, dst_placements):
            if isinstance(placement, Partial):
                self.partial_reduce_ops_in_target.add(placement.reduce_op)

        src_state = self.DistState(src_placements, src_shard_order)
        dst_state = self.DistState(dst_placements, dst_shard_order)
        transform_infos: list[_TransformInfo] = []
        state_path = self.find_min_cost_path(src_state, dst_state)
        for cur_state, nxt_state in itertools.pairwise(state_path):
            # find the mesh_dim that is different between cur_state and nxt_state
            if cur_state.placements != nxt_state.placements:
                update_mesh_dim = -1
                for mesh_dim, (cur_placement, nxt_placement) in enumerate(
                    zip(cur_state.placements, nxt_state.placements)
                ):
                    if cur_placement != nxt_placement:
                        if update_mesh_dim != -1:
                            raise AssertionError(
                                "Multiple mesh_dims are different between cur_state and nxt_state"
                            )
                        update_mesh_dim = mesh_dim
                        logical_shape = self.get_logical_shape(
                            cur_state, mesh_dim, full_tensor_shape
                        )
                        transform_infos.append(
                            _TransformInfo(
                                mesh_dim=update_mesh_dim,
                                src_dst_placements=(cur_placement, nxt_placement),
                                logical_shape=logical_shape,
                            )
                        )

        return transform_infos