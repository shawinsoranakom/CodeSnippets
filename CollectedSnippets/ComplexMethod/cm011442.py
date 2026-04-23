def get_next_state(
        self,
        placements: tuple[Placement, ...],
        tensor_mesh_dim_tuple: ShardOrder,
    ) -> dict["DTensorRedistributePlanner.DistState", float]:
        # We map tensor dimensions to device mesh axes, similar to JAX-style
        # sharding representation. Notation:
        # S(<tensor_dim>)[<list_of_device_dims>] means tensor dimension
        # <tensor_dim> is sharded on the listed device mesh axes, where
        # <list_of_device_dims> is sorted by device order.
        #
        # To generalize to arbitrary dimensionality, we use the following notation:
        #   S(a)[x, ...]   : tensor dimension 'a' is sharded on device mesh axes x, ... (variadic, possibly empty)
        #   SS(a)[x, ...]  : _StridedShard on tensor dimension 'a' on device mesh axes x, ... (variadic, possibly empty)
        #   R[...]         : replicated on the listed device mesh axes (possibly empty)
        #   P[...]         : partial on the listed device mesh axes (possibly empty)
        # The ellipsis '...' denotes a variadic wildcard, i.e., zero or more device mesh axes.
        #
        # Below are possible transitions from one sharding state to another.
        # We use `S` for Shard, `SS` for _StridedShard, `R` for Replicate, and `P` for Partial.
        #
        # Case 1. Shard(a) -> Shard(b), use all-to-all (a2a), applies to:
        #   S(a)[..., x] -> S(b)[..., x]
        #   or
        #   S(a)[..., x, y]S(b)[..., z, k] -> S(a)[..., x]S(b)[..., z, k, y]
        #   where device order of 'y' > device order of 'z' and 'k'
        #
        # Case 2. Shard() -> Replicate(), use all-gather, applies to:
        #   S(a)[..., x, y, z] -> S(a)[..., x, y]
        #
        # Case 3. Partial() -> Replicate(), use all-reduce, applies to:
        #   P[..., x, y] -> P[..., y] or P[..., x]
        #   Note: this case can be disabled because all-reduce technically is not
        #   a primitive since it combines a reduce-scatter + all-gather.
        #
        # Case 4. Replicate() -> Shard(), use chunk, applies to:
        #   S(a)[..., z] -> S(a)[..., z, y] (`a` can be any tensor dim). Note that
        #   'y' must be after 'z'.
        #
        # Case 5. Partial() -> Shard(), use reduce-scatter, applies to:
        #  P[..., x, y] -> P[..., x]S(a)[..., y] or P[..., x, y] -> P[..., y]S(a)[..., x]
        #
        # Case 6. Replicate() -> Partial(), local math op, applies to:
        #   R* -> P[..., x]
        #
        # (TODO) Case 7. _StridedShard(a) -> Shard(b), use all-to-all (a2a), applies to:
        #   SS(a)[..., x] -> S(b)[..., x]
        #
        # Case 8. _StridedShard() -> Replicate(), use all-gather, applies to:
        #   SS(a)[..., x, y, z] -> SS(a)[..., x, y]
        #
        # (TODO) Case 9. Shard(a) -> _StridedShard(b), use all-to-all (a2a), applies to:
        #   S(a)[..., x] -> SS(b)[..., x]
        #
        # (TODO) Case 10. Partial() -> _StridedShard(), use reduce-scatter, applies to:
        #   P[..., x, y] -> P[..., x]SS(a)[..., y] or P[..., x, y] -> P[..., y]SS(a)[..., x]
        #
        # Case 11. Replicate() -> _StridedShard(), use chunk, applies to:
        #   R* -> SS(a)[..., x]
        #
        # NB: Regarding `_StridedShard``, we only allow changing `Replicate` into
        # `_StridedShard` with the same tensor dim and split_factor that occurs in the
        # target placement.
        #
        # (TODO) Verify device order impact in Partial placement. We may need to handle
        # device ordering for Partial also.

        # list of [DistState, cost]
        all_next_state: dict[DTensorRedistributePlanner.DistState, float] = {}

        tensor_mesh_dim_dict = DTensorRedistributePlanner._ShardOrder_to_dict(
            tensor_mesh_dim_tuple
        )
        cur_dist_state = self.DistState(
            self._to_tuple(placements),
            tensor_mesh_dim_tuple,
        )
        ######################################################################
        # handle case 1: Shard(a) -> Shard(b)
        # For S(a), S(b), only the last device order of S(a) and S(b) can be a2a
        # interchangeably.

        # convert sparse tuple
        for entry in tensor_mesh_dim_tuple:
            src_tensor_dim = entry.tensor_dim
            src_mesh_dim = tensor_mesh_dim_dict[src_tensor_dim][-1]
            if not isinstance(placements[src_mesh_dim], Shard):
                # skip special case like `_StridedShard`
                continue
            for dst_tensor_dim in range(self.tensor_dimension):
                if src_tensor_dim == dst_tensor_dim:
                    continue
                # try move the last sharded device dim from
                # Shard(src_tensor_dim) to Shard(dst_tensor_dim)
                move_mesh_dim = tensor_mesh_dim_dict[src_tensor_dim].pop()
                tensor_mesh_dim_dict[dst_tensor_dim].append(move_mesh_dim)
                new_placements = list(placements)
                new_placements[move_mesh_dim] = Shard(dst_tensor_dim)
                dist_state = self.DistState(
                    self._to_tuple(new_placements),
                    DTensorRedistributePlanner._dict_to_ShardOrder(
                        tensor_mesh_dim_dict
                    ),
                )
                all_next_state[dist_state] = self.cost_function(
                    cur_dist_state,
                    dist_state,
                )
                # reset content for next iteration
                tensor_mesh_dim_dict[src_tensor_dim].append(move_mesh_dim)
                tensor_mesh_dim_dict[dst_tensor_dim].pop()
        # TODO(zpcore): support discovering submesh to prevent padding when
        # tensor dim is not divisible by the mesh dim.

        ######################################################################
        # handle case 2: Shard() -> Replicate()
        for entry in tensor_mesh_dim_tuple:
            src_tensor_dim = entry.tensor_dim
            src_mesh_dim = tensor_mesh_dim_dict[src_tensor_dim][-1]
            if not isinstance(placements[src_mesh_dim], Shard):
                # skip special case like `_StridedShard`
                continue
            move_mesh_dim = tensor_mesh_dim_dict[src_tensor_dim].pop()
            new_placements = list(placements)
            new_placements[move_mesh_dim] = Replicate()
            dist_state = self.DistState(
                self._to_tuple(new_placements),
                DTensorRedistributePlanner._dict_to_ShardOrder(tensor_mesh_dim_dict),
            )
            tensor_mesh_dim_dict[src_tensor_dim].append(move_mesh_dim)
            all_next_state[dist_state] = self.cost_function(
                cur_dist_state,
                dist_state,
            )

        ######################################################################
        # handle case 3: Partial() -> Replicate()
        for src_mesh_dim, placement in enumerate(placements):
            if not isinstance(placement, Partial):
                continue
            new_placements = list(placements)
            new_placements[src_mesh_dim] = Replicate()
            dist_state = self.DistState(
                self._to_tuple(new_placements), tensor_mesh_dim_tuple
            )
            all_next_state[dist_state] = self.cost_function(
                cur_dist_state,
                dist_state,
            )

        ######################################################################
        # handle case 4: Replicate() -> Shard()
        for mesh_dim, placement in enumerate(placements):
            if not isinstance(placement, Replicate):
                continue
            for dst_tensor_dim in range(self.tensor_dimension):
                # try convert placement[mesh_dim] to Shard(dst_tensor_dim)
                new_placements = list(placements)
                new_placements[mesh_dim] = Shard(dst_tensor_dim)
                tensor_mesh_dim_dict[dst_tensor_dim].append(mesh_dim)
                dist_state = self.DistState(
                    self._to_tuple(new_placements),
                    DTensorRedistributePlanner._dict_to_ShardOrder(
                        tensor_mesh_dim_dict
                    ),
                )
                all_next_state[dist_state] = self.cost_function(
                    cur_dist_state,
                    dist_state,
                )
                tensor_mesh_dim_dict[dst_tensor_dim].pop()

        ######################################################################
        # handle case 5: Partial() -> Shard()
        for mesh_dim, placement in enumerate(placements):
            if not isinstance(placement, Partial):
                continue
            for dst_tensor_dim in range(self.tensor_dimension):
                # try convert placement[mesh_dim] to Shard(dst_tensor_dim)
                new_placements = list(placements)
                new_placements[mesh_dim] = Shard(dst_tensor_dim)
                tensor_mesh_dim_dict[dst_tensor_dim].append(mesh_dim)
                dist_state = self.DistState(
                    self._to_tuple(new_placements),
                    DTensorRedistributePlanner._dict_to_ShardOrder(
                        tensor_mesh_dim_dict
                    ),
                )
                all_next_state[dist_state] = self.cost_function(
                    cur_dist_state,
                    dist_state,
                )
                tensor_mesh_dim_dict[dst_tensor_dim].pop()

        ######################################################################
        # handle case 6: Replicate() -> Partial()
        # Generate transitions only for reduce_ops that are present in the src/dst
        # placements for this redistribution, avoiding unnecessary graph expansion.
        for mesh_dim, placement in enumerate(placements):
            if not isinstance(placement, Replicate):
                continue
            for reduce_op in self.partial_reduce_ops_in_target:
                new_placements = list(placements)
                new_placements[mesh_dim] = Partial(reduce_op)

                # Skip if this would create mixed partial types (except sum+avg which commute)
                partial_reduce_ops = {
                    p.reduce_op for p in new_placements if isinstance(p, Partial)
                }
                if len(partial_reduce_ops) > 1 and partial_reduce_ops != {"sum", "avg"}:
                    continue

                dist_state = self.DistState(
                    self._to_tuple(new_placements), tensor_mesh_dim_tuple
                )
                all_next_state[dist_state] = self.cost_function(
                    cur_dist_state,
                    dist_state,
                )

        # Additional cases handling for _StridedShard

        ######################################################################
        # TODO(zpcore): handle case 7: _StridedShard() -> Shard() on the same dim

        ######################################################################
        # handle case 8: _StridedShard() -> Replicate()
        for entry in tensor_mesh_dim_tuple:
            src_tensor_dim = entry.tensor_dim
            src_mesh_dim = tensor_mesh_dim_dict[src_tensor_dim][-1]
            if not isinstance(placements[src_mesh_dim], _StridedShard):
                continue
            move_mesh_dim = tensor_mesh_dim_dict[src_tensor_dim].pop()
            new_placements = list(placements)
            new_placements[move_mesh_dim] = Replicate()
            dist_state = self.DistState(
                self._to_tuple(new_placements),
                DTensorRedistributePlanner._dict_to_ShardOrder(tensor_mesh_dim_dict),
            )
            tensor_mesh_dim_dict[src_tensor_dim].append(move_mesh_dim)
            all_next_state[dist_state] = self.cost_function(
                cur_dist_state,
                dist_state,
            )

        # Early exit if no StridedShard in target
        if not self.strided_shard_placements_in_target:
            return all_next_state

        ######################################################################
        # TODO(zpcore): handle case 9: Shard() -> _StridedShard()

        ######################################################################
        # TODO(zpcore): handle case 10: Partial() -> _StridedShard()

        ######################################################################
        # handle case 11: Replicate() -> _StridedShard()
        for mesh_dim, placement in enumerate(placements):
            if not isinstance(placement, Replicate):
                continue
            for strided_shard_obj in self.strided_shard_placements_in_target:
                dst_tensor_dim = strided_shard_obj.dim
                # try convert placement[mesh_dim] to strided_shard_obj
                new_placements = list(placements)
                new_placements[mesh_dim] = strided_shard_obj
                tensor_mesh_dim_dict[dst_tensor_dim].append(mesh_dim)
                dist_state = self.DistState(
                    self._to_tuple(new_placements),
                    DTensorRedistributePlanner._dict_to_ShardOrder(
                        tensor_mesh_dim_dict
                    ),
                )
                all_next_state[dist_state] = self.cost_function(
                    cur_dist_state,
                    dist_state,
                )
                tensor_mesh_dim_dict[dst_tensor_dim].pop()

        return all_next_state