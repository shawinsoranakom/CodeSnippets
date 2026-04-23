def test_add_file_multiple_threads(self):
        """We can safely call `add` from multiple threads simultaneously."""

        def add_file(ii: int) -> None:
            coord = random_coordinates()
            data = bytes(f"{ii}", "utf-8")
            self.media_file_manager.add(data, "image/png", coord)

        call_on_threads(add_file, num_threads=self.NUM_THREADS)
        self.assertEqual(self.NUM_THREADS, len(self.media_file_manager._file_metadata))