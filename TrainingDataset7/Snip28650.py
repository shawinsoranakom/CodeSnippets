def test_deconstruction(self):
        index = models.Index(fields=["title"], db_tablespace="idx_tbls")
        index.set_name_with_model(Book)
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.db.models.Index")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": ["title"],
                "name": "model_index_title_196f42_idx",
                "db_tablespace": "idx_tbls",
            },
        )