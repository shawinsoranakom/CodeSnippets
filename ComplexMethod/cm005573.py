def fork_blocks(
        self, parent_blocks: list[int], num_forks: int, shareable: bool, group_id: int
    ) -> tuple[list[list[int]] | None, list[int], list[int]]:
        """Fork a given list of (parent_blocks) as many times as (num_forks). If the blocks are (shareable), we use
        reference on the blocks that are complete. Otherwise, we allocate new blocks and keep track of their indices to
        later copy the physical cache. For instance, when forking 4 blocks for 2 children:

        Parent blocks: [0, 1, 2, 3], with all blocks being complete except the last one (block 3).

        ----------------------------------------- IF BLOCKS ARE NOT SHAREABLE -----------------------------------------

        Forked blocks lists: [[5, 6, 7, 8], [9, 10, 11, 12]]
        Copy source:          [0, 1, 2, 3,   0,  1,  2,  3]
                               ↓  ↓  ↓  ↓    ↓   ↓   ↓   ↓
        Copy destination:     [5, 6, 7, 8,   9, 10, 11, 12]  → 8 blocks are newly allocated and copied

        ----------------------------------------- IF BLOCKS ARE SHAREABLE ---------------------------------------------

        Forked blocks lists: [[0, 1, 2, 5], [0, 1, 2, 6]]
        Copy source:          [         3,            3]     (block 3 is not complete so it's copied, not referenced)
                                        ↓             ↓
        Copy destination:     [         5,            6]     → only 2 blocks are newly allocated and copied
        """
        # First phase: reference all complete blocks
        forked_by_reference = []

        if shareable:
            for block_id in parent_blocks:
                block = self._id_to_block[block_id]
                if block.is_complete:
                    forked_by_reference.append(block.id)
                    block.ref_count += num_forks
                else:
                    break

        # Early return if we have forked all blocks by reference
        blocks_to_copy = len(parent_blocks) - len(forked_by_reference)
        if blocks_to_copy == 0:
            return [forked_by_reference[:] for _ in range(num_forks)], [], []

        # From now on, each child will have its own list of blocks
        forked_blocks_lists = []
        copy_src = []
        copy_dst = []

        # Second phase: allocate new blocks if needed
        parent_id = forked_by_reference[-1] if forked_by_reference else None
        for _ in range(num_forks):
            allocated_block_ids = self.get_free_blocks(blocks_to_copy, parent_id, shareable, group_id)
            if allocated_block_ids is None:
                return None, [], []
            forked_blocks_lists.append(forked_by_reference + allocated_block_ids)
            copy_src.extend(parent_blocks[-blocks_to_copy:])
            copy_dst.extend(allocated_block_ids)
        return forked_blocks_lists, copy_src, copy_dst