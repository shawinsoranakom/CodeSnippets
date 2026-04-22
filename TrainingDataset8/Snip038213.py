def get_stats(self) -> List[CacheStat]:
        """Return the manager's CacheStats.

        Safe to call from any thread.
        """
        with self._files_lock:
            # Flatten all files into a single list
            all_files: List[UploadedFileRec] = []
            for file_list in self._files_by_id.values():
                all_files.extend(file_list)

        return [
            CacheStat(
                category_name="UploadedFileManager",
                cache_name="",
                byte_length=len(file.data),
            )
            for file in all_files
        ]