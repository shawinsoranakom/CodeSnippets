def test_intermediate_files(self):
        cached_files = os.listdir(os.path.join(settings.STATIC_ROOT, "cached"))
        # Intermediate files shouldn't be created for reference.
        self.assertEqual(
            len(
                [
                    cached_file
                    for cached_file in cached_files
                    if cached_file.startswith("relative.")
                ]
            ),
            2,
        )