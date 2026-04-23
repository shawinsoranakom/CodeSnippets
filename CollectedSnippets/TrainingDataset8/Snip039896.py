def test_os_environ(self, _):
        """os.environ gets patched when we load our secrets.toml"""
        # We haven't loaded secrets yet
        self.assertEqual(os.environ.get("db_username"), None)

        self.secrets.load_if_toml_exists()
        self.assertEqual(os.environ["db_username"], "Jane")
        self.assertEqual(os.environ["db_password"], "12345qwerty")

        # Subsections do not get loaded into os.environ
        self.assertEqual(os.environ.get("subsection"), None)