def test_remove_orphaned_files(
        self, get_file_recs_patch, remove_orphaned_files_patch
    ):
        """When file_uploader is accessed, it should call
        UploadedFileManager.remove_orphaned_files.
        """
        ctx = get_script_run_ctx()
        ctx.uploaded_file_mgr._file_id_counter = 101

        file_recs = [
            UploadedFileRec(1, "file1", "type", b"123"),
            UploadedFileRec(2, "file2", "type", b"456"),
        ]
        get_file_recs_patch.return_value = file_recs

        st.file_uploader("foo", accept_multiple_files=True)

        args, kwargs = remove_orphaned_files_patch.call_args
        self.assertEqual(len(args), 0)
        self.assertEqual(kwargs["session_id"], "test session id")
        self.assertEqual(kwargs["newest_file_id"], 100)
        self.assertEqual(kwargs["active_file_ids"], [1, 2])

        # Patch _get_file_recs to return [] instead. remove_orphaned_files
        # should not be called when file_uploader is accessed.
        get_file_recs_patch.return_value = []
        remove_orphaned_files_patch.reset_mock()

        st.file_uploader("foo")
        remove_orphaned_files_patch.assert_not_called()