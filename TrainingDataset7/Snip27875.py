def test_move_temporary_file(self):
        """
        The temporary uploaded file is moved rather than copied to the
        destination.
        """
        with TemporaryUploadedFile(
            "something.txt", "text/plain", 0, "UTF-8"
        ) as tmp_file:
            tmp_file_path = tmp_file.temporary_file_path()
            Document.objects.create(myfile=tmp_file)
            self.assertFalse(
                os.path.exists(tmp_file_path), "Temporary file still exists"
            )