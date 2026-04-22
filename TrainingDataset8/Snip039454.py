def test_Credentials_save(self):
        """Test Credentials.save()."""
        c = Credentials.get_current()
        c.activation = _Activation("some_email", True)
        truth = textwrap.dedent(
            """
            [general]
            email = "some_email"
        """
        ).lstrip()

        streamlit_root_path = os.path.join(
            "/mock/home/folder", file_util.CONFIG_FOLDER_NAME
        )

        # patch streamlit.*.os.makedirs instead of os.makedirs for py35 compat
        with patch(
            "streamlit.runtime.credentials.open", mock_open(), create=True
        ) as open, patch("streamlit.runtime.credentials.os.makedirs") as make_dirs:

            c.save()

            make_dirs.assert_called_once_with(streamlit_root_path, exist_ok=True)
            open.return_value.write.assert_called_once_with(truth)