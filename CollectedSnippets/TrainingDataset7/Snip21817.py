def test_filefield_generate_filename_with_upload_to(self):
        def upload_to(instance, filename):
            return "some/folder/" + filename

        f = FileField(upload_to=upload_to)
        self.assertEqual(
            f.generate_filename(None, "test with space.txt"),
            os.path.normpath("some/folder/test_with_space.txt"),
        )