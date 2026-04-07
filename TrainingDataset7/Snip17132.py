def test_aggregate_duplicate_columns_select_related(self):
        # And select_related()
        results = Book.objects.select_related("contact").annotate(
            num_authors=Count("authors")
        )
        _, _, grouping = results.query.get_compiler(using="default").pre_sql_setup()
        self.assertEqual(len(grouping), 2)
        self.assertIn("id", grouping[0][0])
        self.assertNotIn("name", grouping[0][0])
        self.assertNotIn("contact", grouping[0][0])
        self.assertEqual(
            [(b.name, b.num_authors) for b in results.order_by("name")],
            [
                ("Artificial Intelligence: A Modern Approach", 2),
                (
                    "Paradigms of Artificial Intelligence Programming: Case Studies in "
                    "Common Lisp",
                    1,
                ),
                ("Practical Django Projects", 1),
                ("Python Web Development with Django", 3),
                ("Sams Teach Yourself Django in 24 Hours", 1),
                ("The Definitive Guide to Django: Web Development Done Right", 2),
            ],
        )