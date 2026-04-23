def mark_shareable_blocks_as_complete(
        self, num_complete_blocks: int, allocated_blocks: list[int], prompt_ids: list[int]
    ) -> None:
        """Among the list of (allocated_blocks), mark (num_complete_blocks) incomplete blocks as now complete. The list
        of (prompt_ids) is used to compute the hash of the new block."""
        # Look for the first complete block, starting from the last block in the sequence
        parent_hash = None
        incomplete_blocks: list[tuple[int, Block]] = []
        for i, block_id in reverse_enumerate(allocated_blocks):
            block = self._id_to_block[block_id]
            if block.is_complete:
                parent_hash = block.hash
                break
            incomplete_blocks.append((i, block))

        # Now go through the incomplete blocks and updated them
        new_parent_id = None
        while incomplete_blocks:
            i, block = incomplete_blocks.pop()

            # If the parent id has been updated, we apply the change
            if new_parent_id is not None:
                block.parent_id = new_parent_id
                new_parent_id = None

            # If we have set the hash for all complete blocks, we can stop
            if num_complete_blocks == 0:
                break

            # Otherwise, we compute the hash
            num_complete_blocks -= 1
            tokens = prompt_ids[i * self.block_size : (i + 1) * self.block_size]
            block.hash = self.compute_hash(parent_hash, tokens, block.group_id)

            existing_block_id = self._hash_to_id.get(block.hash)
            # If their was a different block with the same hash, we reference the existing block instead
            if existing_block_id is not None:
                if existing_block_id == block.id:
                    # This should not happen, but is not a problem in itself, so we just log a warning
                    logger.warning(f"Block {block.id} was marked as complete more than once")
                else:
                    logger.debug(f"Found existing block {existing_block_id} for block {block.id}")
                    allocated_blocks[i] = existing_block_id
                    new_parent_id = existing_block_id
                    self.increase_ref_count(existing_block_id)
                    self.uninitialize_unshared_block(block.id)

            # Otherwise, we add the completed block to the hash table
            else:
                logger.debug(f"Adding new block {block.id} (group {block.group_id}) with hash {block.hash}")
                self._hash_to_id[block.hash] = block.id

            # Update loop variables
            parent_hash = block.hash