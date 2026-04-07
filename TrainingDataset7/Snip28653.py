def test_deconstruct_with_expressions(self):
        index = models.Index(Upper("title"), name="book_func_idx")
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.db.models.Index")
        self.assertEqual(args, (Upper("title"),))
        self.assertEqual(kwargs, {"name": "book_func_idx"})