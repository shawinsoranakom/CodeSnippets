def test_file_chunks_error(self):
        """
        Test behavior when file.chunks() is raising an error
        """
        f1 = ContentFile("chunks fails")

        def failing_chunks():
            raise OSError

        f1.chunks = failing_chunks
        with self.assertRaises(OSError):
            self.storage.save("error.file", f1)