def test_file_path_field(self):
        field = models.FilePathField(match=r".*\.txt$")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.FilePathField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"match": r".*\.txt$"})
        field = models.FilePathField(recursive=True, allow_folders=True, max_length=123)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.FilePathField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs, {"recursive": True, "allow_folders": True, "max_length": 123}
        )