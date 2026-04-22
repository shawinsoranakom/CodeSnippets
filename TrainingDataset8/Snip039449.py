def test_Credentials_load_file_not_found(self):
        """Test Credentials.load() with FileNotFoundError."""
        with patch("streamlit.runtime.credentials.open") as m:
            m.side_effect = FileNotFoundError()
            c = Credentials.get_current()
            c.activation = None
            with pytest.raises(RuntimeError) as e:
                c.load()
            self.assertEqual(
                str(e.value), 'Credentials not found. Please run "streamlit activate".'
            )