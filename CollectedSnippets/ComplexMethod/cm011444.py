def generate_greedy_transform_infos(
        self,
        src_spec: DTensorSpec,
        dst_spec: DTensorSpec,
    ) -> list[_TransformInfo]:
        """
        Generate the transform infos from the source placements to the target placements.

        To transform from source to target placement it might have multiple steps, i.e. it
        might decompose Si -> Sj into Si -> R -> Sj.
        This would detect if there're mis-aligned/nested shardings between src/dst placements.
        E.g. Suppose the redistribution to perform is (Shard(0), Shard(0)) -> (Replicate(), Shard(0)),
        in this case Shard(0) -> Shard(0) for mesh dimension 1 actually needs resharding, because in
        the former is a nested-sharding of a tensor already already sharded dimension 0, whereas
        the latter is the first sharding on tensor dimension 0.
        """
        # logical shape records the logic tensor shape on the mesh dimension
        # this is useful to ensure uneven sharding gets correct output shape
        initial_logical_shape = list(src_spec.shape)
        mesh_dims_to_logical_shape = [initial_logical_shape]
        transform_infos: list[_TransformInfo] = []
        if self.device_mesh.ndim == 1:
            # if device_mesh is 1D, redistribute is a simple direct
            # transformation (skip if src == dst)
            if src_spec.placements[0] != dst_spec.placements[0]:
                transform_infos.append(
                    _TransformInfo(
                        mesh_dim=0,
                        src_dst_placements=(
                            src_spec.placements[0],
                            dst_spec.placements[0],
                        ),
                        logical_shape=initial_logical_shape,
                    )
                )
            return transform_infos

        # Handle multi-dim device mesh placement redistribution First, we need
        # to build the logical shape for each mesh dim for correct allgather
        # uneven shards on each mesh dim (with dynamic padding)
        for i, src in enumerate(src_spec.placements):
            current_logical_shape = mesh_dims_to_logical_shape[i]
            if isinstance(src, Shard):
                if i < self.device_mesh.ndim - 1:
                    # calculate and save the logical shape for this sharding
                    mesh_dim_size = self.device_mesh.size(mesh_dim=i)
                    local_shard_size, _ = src._local_shard_size_and_offset(
                        current_logical_shape[src.dim],
                        mesh_dim_size,
                        self.device_mesh._sym_get_coordinate(i),
                    )
                    new_logical_shape = list(current_logical_shape)
                    new_logical_shape[src.dim] = local_shard_size
                    mesh_dims_to_logical_shape.append(new_logical_shape)
            else:
                mesh_dims_to_logical_shape.append(current_logical_shape)

        # Next, we need to derive the transform infos from src to dst
        # placements, here we use a greedy search with step by step state
        # transformations
        current_placements = list(src_spec.placements)
        target_placements = list(dst_spec.placements)

        if src_spec.num_shards > 1:
            # If src_spec have sharding, it could potentially have sharding that
            # is misaligned with dst_spec a common case of this is nested
            # sharding (i.e. (S(0), S(0)) -> (R, S(0))). In those cases, we
            # first traverse from inner placement to outer placement to detect
            # misaligned shardings and properly replicate nested sharding first.
            for mesh_dim in reversed(range(len(current_placements))):
                current = current_placements[mesh_dim]
                target = target_placements[mesh_dim]
                # If target is not Shard, we can directly redistribute since we
                # are traversing from inner to outer placements here
                # TODO: extend nested sharding detection to _StridedShard
                # (isinstance check and is_shard() below miss it).
                # Safe today: strategies convert _StridedShard to Replicate
                # on ALL mesh dims for a given reduction dim, so misaligned
                # nested _StridedShard targets can't arise.
                if isinstance(target, Shard):
                    # If target is Shard, check for nested sharding on the
                    # tensor dim BEFORE the current mesh_dim
                    shard_dim = target.dim
                    current_mesh_sharding, target_mesh_sharding = [], []
                    for i, (s, p) in enumerate(
                        zip(current_placements, target_placements)
                    ):
                        if i >= mesh_dim:
                            break
                        if s.is_shard(shard_dim):
                            current_mesh_sharding.append(i)
                        if p.is_shard(shard_dim):
                            target_mesh_sharding.append(i)

                    if current_mesh_sharding != target_mesh_sharding:
                        # if current/target_placements have misaligned sharding
                        # on the tensor dim BEFORE the current mesh_dim, we need
                        # to replicate the tensor on the mesh dim first to clear
                        # the nested sharding
                        target = Replicate()

                if current != target:
                    transform_infos.append(
                        _TransformInfo(
                            mesh_dim=mesh_dim,
                            src_dst_placements=(current, target),
                            logical_shape=mesh_dims_to_logical_shape[mesh_dim],
                        )
                    )
                    current_placements[mesh_dim] = target

        # We always traverse from outer placement to inner placement to collect
        # the remaining needed transform infos (i.e. the replication from nested
        # sharding might need to further perform resharding to Shard again)
        for mesh_dim, (current, target) in enumerate(
            zip(current_placements, target_placements)
        ):
            if current != target:
                transform_infos.append(
                    _TransformInfo(
                        mesh_dim=mesh_dim,
                        src_dst_placements=(current, target),
                        logical_shape=mesh_dims_to_logical_shape[mesh_dim],
                    )
                )
                current_placements[mesh_dim] = target
        return transform_infos