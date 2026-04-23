def test_deconstruction(self):
        index = BTreeIndex(fields=["title"], name="test_title_btree")
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.indexes.BTreeIndex")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"fields": ["title"], "name": "test_title_btree"})

        index = BTreeIndex(
            fields=["title"],
            name="test_title_btree",
            fillfactor=80,
            deduplicate_items=False,
        )
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.indexes.BTreeIndex")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": ["title"],
                "name": "test_title_btree",
                "fillfactor": 80,
                "deduplicate_items": False,
            },
        )