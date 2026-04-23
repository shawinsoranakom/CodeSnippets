def test_Credentials_load_permission_denied(self):
        """Test Credentials.load() with Perission denied."""
        with patch("streamlit.runtime.credentials.open") as m:
            m.side_effect = PermissionError(
                "[Errno 13] Permission denied: ~/.streamlit/credentials.toml"
            )
            c = Credentials.get_current()
            c.activation = None
            with pytest.raises(Exception) as e:
                c.load()
            self.assertEqual(
                str(e.value).split(":")[0],
                "\nUnable to load credentials from "
                "/mock/home/folder/.streamlit/credentials.toml.\n"
                'Run "streamlit reset" and try again.\n',
            )