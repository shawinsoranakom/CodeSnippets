def test_callable_path(self):
        path = os.path.dirname(__file__)

        def generate_path():
            return path

        field = FilePathField(path=generate_path)
        self.assertEqual(field.path(), path)
        self.assertEqual(field.formfield().path, path)