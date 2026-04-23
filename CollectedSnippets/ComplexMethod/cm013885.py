def update_block_stack(self, inst: Instruction) -> None:
            # 3.11+ no longer uses a block stack, but we still keep track of one
            # so that we know which contexts are currently active.
            # For our purposes, all exception table entries with the same target
            # are considered to be part of the same "block".
            # NOTE: we only keep track of with blocks that are not contained in try blocks.
            # This is because we will not create continuation functions on graph breaks in try blocks,
            # but we may for with blocks. We do not push blocks here since
            # with blocks are pushed when handling BEFORE_WITH.
            entry = inst.exn_tab_entry
            if entry:
                # Detect when we have exited the top with block.
                # The with blocks on the block stack are not enclosed in try
                # blocks, so a with block's cleanup code should be in the
                # previous with block (if any).
                if (
                    len(self.block_stack) >= 2
                    and entry.target is not self.block_stack[-1].target
                    and entry.target is self.block_stack[-2].target
                ):
                    # exit the current block
                    self.block_stack.pop()
            else:
                # no longer in any block
                # It is possible for NOPs to be between two instructions
                # in the same block, but the NOPs are not covered by an
                # exception table entry. In this case, assume that we
                # are still in the same block.
                # In 3.12+, JUMP_BACKWARD might also not be covered by
                # an exception table entry, so we also assume that we
                # are still in the same block. It is probably safe to do
                # this in 3.11, even though we haven't encountered this case before.
                # In 3.14+, NOT_TAKEN might also not be covered by an exn table entry.
                if self.block_stack and inst.opname not in (
                    "NOP",
                    "JUMP_BACKWARD",
                    "NOT_TAKEN",
                ):
                    # If we really escape from a block and the current
                    # instruction is not in another block, then there
                    # should be no other nested blocks that we are in.
                    assert len(self.block_stack) == 1
                    self.block_stack.pop()