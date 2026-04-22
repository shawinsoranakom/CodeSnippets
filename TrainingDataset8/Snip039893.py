def test_repr_secrets(self, runtime_exists, secrets_repr, *mocks):
        with patch("streamlit.runtime.exists", return_value=runtime_exists):
            self.assertEqual(repr(self.secrets), secrets_repr)