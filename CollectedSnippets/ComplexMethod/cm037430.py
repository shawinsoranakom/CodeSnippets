def evict(
        self, n: int, protected: set[OffloadKey]
    ) -> list[tuple[OffloadKey, BlockStatus]] | None:
        if n == 0:
            return []
        candidates: list[tuple[OffloadKey, BlockStatus]] = []
        for key, block in self.blocks.items():
            if block.ref_cnt == 0 and key not in protected:
                candidates.append((key, block))
                if len(candidates) == n:
                    break
        if len(candidates) < n:
            return None
        for key, _ in candidates:
            del self.blocks[key]
        return candidates