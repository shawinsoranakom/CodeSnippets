def _set_post_op_offset(self, state, spec, old_offset) -> None:
        """Set per-rank offsets after the random operation."""
        from torch.distributed.tensor._ops.utils import prod

        lm = enabled_local_tensor_mode()
        if lm is None:
            raise AssertionError

        dtensor_shape = spec.shape
        numel = prod(dtensor_shape)
        # offset must be multiple of 4
        numel = (numel + 3) // 4 * 4

        if not hasattr(state, "_per_rank_offsets"):
            state._per_rank_offsets = {}

        # handle LocalIntNode old_offset (different values per rank)
        if isinstance(old_offset, SymInt) and isinstance(old_offset.node, LocalIntNode):
            for rank in lm.ranks:
                rank_old_offset = old_offset.node._local_ints[rank]
                state._per_rank_offsets[rank] = rank_old_offset + numel
        else:
            # same old_offset for all ranks
            old_offset_int = (
                int(old_offset) if isinstance(old_offset, SymInt) else old_offset
            )
            for rank in lm.ranks:
                state._per_rank_offsets[rank] = old_offset_int + numel