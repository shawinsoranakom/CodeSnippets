def allocate_pages_for_keys(
        self, rank: int, keys: list[tuple[str, str]]
    ) -> dict[str, int]:
        """Allocate one page for each key on the specified rank.

        Args:
            rank: Rank ID to allocate pages on
            keys: List of keys to allocate pages for

        Returns:
            Dictionary mapping key -> allocated page index
        """
        with self.global_lock:
            if rank not in self.rank_metadata:
                raise ValueError(f"Rank {rank} not initialized")

            # Batch allocate pages for all keys
            num_pages_needed = len(keys)
            allocated_pages = self.rank_metadata[rank].allocate_pages(num_pages_needed)

            if len(allocated_pages) < num_pages_needed:
                logger.warning(
                    "Rank %s only allocated %s pages for %s keys",
                    rank,
                    len(allocated_pages),
                    num_pages_needed,
                )

            allocation_results = {}
            for i, (key, prefix_key) in enumerate(keys):
                if key in self.key_metadata:
                    key_meta = self.key_metadata[key]
                    if key_meta.is_complete() and rank in key_meta.rank_to_page:
                        # key is already fully written, reuse the existing page
                        # and release the allocated pages back to the free pool.
                        if i < len(allocated_pages):
                            self.rank_metadata[rank].release_pages([allocated_pages[i]])
                        allocation_results[key] = key_meta.rank_to_page[rank]
                        continue

                if i < len(allocated_pages):
                    allocation_results[key] = allocated_pages[i]
                else:
                    allocation_results[key] = -1  # No pages available

            return allocation_results