def test_unique_uploaded_file_instance(self, get_file_recs_patch):
        """We should get a unique UploadedFile instance each time we access
        the file_uploader widget."""

        # Patch UploadFileManager to return two files
        file_recs = [
            UploadedFileRec(1, "file1", "type", b"123"),
            UploadedFileRec(2, "file2", "type", b"456"),
        ]

        get_file_recs_patch.return_value = file_recs

        # These file_uploaders have different labels so that we don't cause
        # a DuplicateKey error - but because we're patching the get_files
        # function, both file_uploaders will refer to the same files.
        file1: UploadedFile = st.file_uploader("a", accept_multiple_files=False)
        file2: UploadedFile = st.file_uploader("b", accept_multiple_files=False)

        self.assertNotEqual(id(file1), id(file2))

        # Seeking in one instance should not impact the position in the other.
        file1.seek(2)
        self.assertEqual(b"3", file1.read())
        self.assertEqual(b"123", file2.read())