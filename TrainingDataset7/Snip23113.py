def test_init_with_src_kwarg(self):
        self.assertEqual(
            Script(src="path/to/js").path, "http://media.example.com/static/path/to/js"
        )