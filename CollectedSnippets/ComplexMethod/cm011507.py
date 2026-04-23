def _derive_follow_placements_from_tuple_strategy(
    op: torch._ops.OpOverload,
    tuple_strategy: TupleStrategy,
) -> Sequence[Placement]:
    """
    derive the placements to follow from the tuple strategy, mainly used by
    aten.stack, aten.cat, where each operand have the same shape, and correspondingly
    expecting the same sharding
    """

    def merge_placement(
        cur_placement: Placement, new_placement: Placement
    ) -> Placement:
        # semantic if we already have a follow placement, we
        # check each placement for the current arg placement
        # to see if we want to merge/adjust the placement to follow
        # the priority: Partial -> Shard -> Replicate
        # _StridedShard.__eq__ compares both dim and split_factor,
        # so two _StridedShard with different split_factor won't match here.
        if cur_placement == new_placement:
            return cur_placement

        if cur_placement.is_partial():
            if _is_shard_like(new_placement):
                # follow new placement
                return new_placement
            elif new_placement.is_partial():
                # different partial types, we can't merge and have to replicate all here
                return Replicate()
            else:
                # follow partial
                return cur_placement
        elif _is_shard_like(cur_placement):
            if _is_shard_like(new_placement):
                # cur/new placement are different sharding (i.e. different shard dim)
                # currently fallback to replicate all args
                return Replicate()
            else:
                # for partial/replicate, follow the current shard placement
                return cur_placement
        else:
            # current replicate, just follow new placement
            return new_placement

    follow_placements: list[Placement] | None = None
    mesh = tuple_strategy.child_mesh(0)
    for arg_strategy in tuple_strategy.children:
        if not isinstance(arg_strategy, OpStrategy):
            raise AssertionError(f"Expected OpStrategy, got {type(arg_strategy)}")
        if arg_strategy.mesh != mesh:
            raise ValueError(
                f"All operands in {op} must have the same mesh, "
                f"but got {arg_strategy.mesh} and {mesh}."
            )

        for placement_strategy in arg_strategy.strategies:
            arg_placements = placement_strategy.output_spec.placements
            if follow_placements is None:
                follow_placements = list(arg_placements)
                continue
            if follow_placements is None:
                raise AssertionError(
                    "follow_placements should not be None at this point"
                )
            for mesh_idx in range(mesh.ndim):
                # merge placements with the priority
                follow_placements[mesh_idx] = merge_placement(
                    follow_placements[mesh_idx], arg_placements[mesh_idx]
                )
    if follow_placements is None:
        raise AssertionError("follow placements should not be None!")
    return follow_placements