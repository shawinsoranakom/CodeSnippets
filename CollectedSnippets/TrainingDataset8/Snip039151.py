def test_get_project_streamlit_file_path(self):
        expected = os.path.join(
            os.getcwd(), file_util.CONFIG_FOLDER_NAME, "some/random/file"
        )

        self.assertEqual(
            expected, file_util.get_project_streamlit_file_path("some/random/file")
        )

        self.assertEqual(
            expected,
            file_util.get_project_streamlit_file_path("some", "random", "file"),
        )