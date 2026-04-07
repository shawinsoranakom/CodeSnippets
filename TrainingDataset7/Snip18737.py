def test_init_command(self):
        settings_dict = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
                "OPTIONS": {
                    "init_command": "PRAGMA synchronous=3; PRAGMA cache_size=2000;",
                },
            }
        }
        connections = ConnectionHandler(settings_dict)
        connections["default"].ensure_connection()
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("PRAGMA synchronous")
                value = cursor.fetchone()[0]
                self.assertEqual(value, 3)
                cursor.execute("PRAGMA cache_size")
                value = cursor.fetchone()[0]
                self.assertEqual(value, 2000)
        finally:
            connections["default"]._close()