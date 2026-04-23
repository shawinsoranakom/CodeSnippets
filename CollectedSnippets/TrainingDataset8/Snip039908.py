def access_secrets(_: int) -> None:
            self.assertEqual(self.secrets["db_username"], "Jane")
            self.assertEqual(self.secrets["subsection"]["email"], "eng@streamlit.io")
            self.assertEqual(self.secrets["subsection"].email, "eng@streamlit.io")