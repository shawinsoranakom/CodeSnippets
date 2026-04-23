def test_pathlib_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_dict = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": Path(tmp) / "test.db",
                },
            }
            connections = ConnectionHandler(settings_dict)
            connections["default"].ensure_connection()
            connections["default"].close()
            self.assertTrue(os.path.isfile(os.path.join(tmp, "test.db")))