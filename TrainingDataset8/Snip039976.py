def test_file_uploader_serde(self, get_file_recs_patch):
        file_recs = [
            UploadedFileRec(1, "file1", "type", b"123"),
        ]
        get_file_recs_patch.return_value = file_recs

        uploaded_file = st.file_uploader("file_uploader", key="file_uploader")
        check_roundtrip("file_uploader", uploaded_file)