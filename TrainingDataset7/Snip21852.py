def test_deconstruction(self):
        path, args, kwargs = temp_storage.deconstruct()
        self.assertEqual(path, "django.core.files.storage.FileSystemStorage")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"location": temp_storage_location})

        kwargs_orig = {
            "location": temp_storage_location,
            "base_url": "http://myfiles.example.com/",
        }
        storage = FileSystemStorage(**kwargs_orig)
        path, args, kwargs = storage.deconstruct()
        self.assertEqual(kwargs, kwargs_orig)