def evict(
        self, n: int, protected: set[OffloadKey]
    ) -> list[tuple[OffloadKey, BlockStatus]] | None:
        if n == 0:
            return []

        # Collect candidates atomically: simulate T1 size changes as we select,
        # but do not modify actual data structures until all n are found.
        candidates: list[
            tuple[OffloadKey, BlockStatus, bool]
        ] = []  # (key, block, from_t1)
        already_selected: set[OffloadKey] = set()
        virtual_t1_size = len(self.t1)

        for _ in range(n):
            candidate: tuple[OffloadKey, BlockStatus, bool] | None = None

            if virtual_t1_size >= int(self.target_t1_size):
                for key, block in self.t1.items():
                    if (
                        block.ref_cnt == 0
                        and key not in protected
                        and key not in already_selected
                    ):
                        candidate = (key, block, True)
                        virtual_t1_size -= 1
                        break

            if candidate is None:
                for key, block in self.t2.items():
                    if (
                        block.ref_cnt == 0
                        and key not in protected
                        and key not in already_selected
                    ):
                        candidate = (key, block, False)
                        break
                if candidate is None:
                    return None

            candidates.append(candidate)
            already_selected.add(candidate[0])

        # Apply all evictions now that we know n candidates exist.
        result: list[tuple[OffloadKey, BlockStatus]] = []
        for key, block, from_t1 in candidates:
            if from_t1:
                del self.t1[key]
                self.b1[key] = None
            else:
                del self.t2[key]
                self.b2[key] = None
            result.append((key, block))

        # Trim ghost lists to cache_capacity.
        for ghost in (self.b1, self.b2):
            for _ in range(len(ghost) - self.cache_capacity):
                ghost.popitem(last=False)

        return result