def test_filefield_generate_filename(self):
        f = FileField(upload_to="some/folder/")
        self.assertEqual(
            f.generate_filename(None, "test with space.txt"),
            os.path.normpath("some/folder/test_with_space.txt"),
        )