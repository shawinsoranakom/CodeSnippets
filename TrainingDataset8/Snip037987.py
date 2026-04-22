def get_stats(self) -> List[CacheStat]:
        # We operate on a copy of our dict, to avoid race conditions
        # with other threads that may be manipulating the cache.
        files_by_id = self._files_by_id.copy()

        stats: List[CacheStat] = []
        for file_id, file in files_by_id.items():
            stats.append(
                CacheStat(
                    category_name="st_memory_media_file_storage",
                    cache_name="",
                    byte_length=len(file.content),
                )
            )
        return stats