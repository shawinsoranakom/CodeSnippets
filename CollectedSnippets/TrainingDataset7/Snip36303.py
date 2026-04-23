def test_filepath_to_uri(self):
        self.assertIsNone(filepath_to_uri(None))
        self.assertEqual(
            filepath_to_uri("upload\\чубака.mp4"),
            "upload/%D1%87%D1%83%D0%B1%D0%B0%D0%BA%D0%B0.mp4",
        )
        self.assertEqual(filepath_to_uri(Path("upload/test.png")), "upload/test.png")
        self.assertEqual(filepath_to_uri(Path("upload\\test.png")), "upload/test.png")