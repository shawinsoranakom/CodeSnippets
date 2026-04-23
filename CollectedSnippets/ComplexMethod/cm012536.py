def allocate(self, block: Allocation, is_last: bool):
        if (
            self.restrict_live_range is not None
            and not self.restrict_live_range.contains(block.live_range)
        ):
            return False

        block_earliest_available = block.get_earliest_available()
        pool_begin = self.root.get_live_ranges().begin
        if block_earliest_available and block_earliest_available > pool_begin:
            return False

        is_last = self.can_expand and is_last
        if self.root.allocate(block, is_last):
            self.update_restrict_live_range(block)
            return True

        if is_last:
            return self.allocate_at_end(block)

        return False