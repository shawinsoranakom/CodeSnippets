def test_deconstruction(self):
        storage = InMemoryStorage()
        path, args, kwargs = storage.deconstruct()
        self.assertEqual(path, "django.core.files.storage.InMemoryStorage")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})

        kwargs_orig = {
            "location": "/custom_path",
            "base_url": "http://myfiles.example.com/",
            "file_permissions_mode": "0o755",
            "directory_permissions_mode": "0o600",
        }
        storage = InMemoryStorage(**kwargs_orig)
        path, args, kwargs = storage.deconstruct()
        self.assertEqual(kwargs, kwargs_orig)