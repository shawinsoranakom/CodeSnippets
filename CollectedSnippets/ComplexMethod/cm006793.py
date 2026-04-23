def load_files_base(self) -> list[Data]:
        """Loads and parses file(s), including unpacked file bundles.

        Returns:
            list[Data]: Parsed data from the processed files.
        """
        self._temp_dirs: list[TemporaryDirectory] = []
        final_files = []  # Initialize to avoid UnboundLocalError
        try:
            # Step 1: Validate the provided paths
            files = self._validate_and_resolve_paths()

            # Step 2: Handle bundles recursively
            all_files = self._unpack_and_collect_files(files)

            # Step 3: Final validation of file types
            final_files = self._filter_and_mark_files(all_files)

            # Step 4: Process files
            processed_files = self.process_files(final_files)

            # Extract and flatten Data objects to return
            return [data for file in processed_files for data in file.data if file.data]

        finally:
            # Delete temporary directories
            for temp_dir in self._temp_dirs:
                temp_dir.cleanup()
            # Delete files marked for deletion
            for file in final_files:
                if file.delete_after_processing and file.path.exists():
                    if file.path.is_dir():
                        shutil.rmtree(file.path)
                    else:
                        file.path.unlink()