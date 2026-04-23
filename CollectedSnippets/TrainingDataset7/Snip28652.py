def test_deconstruct_with_include(self):
        index = models.Index(
            name="book_include_idx",
            fields=["title"],
            include=["author"],
        )
        index.set_name_with_model(Book)
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.db.models.Index")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": ["title"],
                "name": "model_index_title_196f42_idx",
                "include": ("author",),
            },
        )