def test_deconstruct_with_condition(self):
        index = models.Index(
            name="big_book_index",
            fields=["title"],
            condition=models.Q(pages__gt=400),
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
                "condition": models.Q(pages__gt=400),
            },
        )