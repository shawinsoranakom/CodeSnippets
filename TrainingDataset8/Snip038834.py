def test_multiple_files(self, get_file_recs_patch):
        """Test the accept_multiple_files flag"""
        # Patch UploadFileManager to return two files
        file_recs = [
            UploadedFileRec(1, "file1", "type", b"123"),
            UploadedFileRec(2, "file2", "type", b"456"),
        ]

        get_file_recs_patch.return_value = file_recs

        for accept_multiple in [True, False]:
            return_val = st.file_uploader(
                "label", type="png", accept_multiple_files=accept_multiple
            )
            c = self.get_delta_from_queue().new_element.file_uploader
            self.assertEqual(accept_multiple, c.multiple_files)

            # If "accept_multiple_files" is True, then we should get a list of
            # values back. Otherwise, we should just get a single value.

            # Because file_uploader returns unique UploadedFile instances
            # each time it's called, we convert the return value back
            # from UploadedFile -> UploadedFileRec (which implements
            # equals()) to test equality.

            if accept_multiple:
                results = [
                    UploadedFileRec(file.id, file.name, file.type, file.getvalue())
                    for file in return_val
                ]
                self.assertEqual(file_recs, results)
            else:
                results = UploadedFileRec(
                    return_val.id,
                    return_val.name,
                    return_val.type,
                    return_val.getvalue(),
                )
                self.assertEqual(file_recs[0], results)