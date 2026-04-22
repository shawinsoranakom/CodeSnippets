def get_stats(self) -> List[CacheStat]:
        stats: List[CacheStat] = []
        for entry_hash, entry in self._entries.items():
            stats.append(
                CacheStat(
                    category_name="ForwardMessageCache",
                    cache_name="",
                    byte_length=entry.msg.ByteSize(),
                )
            )
        return stats