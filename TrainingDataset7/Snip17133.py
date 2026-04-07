def test_aggregate_unmanaged_model_columns(self):
        """
        Unmanaged models are sometimes used to represent database views which
        may not allow grouping by selected primary key.
        """

        def assertQuerysetResults(queryset):
            self.assertEqual(
                [(b.name, b.num_authors) for b in queryset.order_by("name")],
                [
                    ("Artificial Intelligence: A Modern Approach", 2),
                    (
                        "Paradigms of Artificial Intelligence Programming: Case "
                        "Studies in Common Lisp",
                        1,
                    ),
                    ("Practical Django Projects", 1),
                    ("Python Web Development with Django", 3),
                    ("Sams Teach Yourself Django in 24 Hours", 1),
                    ("The Definitive Guide to Django: Web Development Done Right", 2),
                ],
            )

        queryset = Book.objects.select_related("contact").annotate(
            num_authors=Count("authors")
        )
        # Unmanaged origin model.
        with mock.patch.object(Book._meta, "managed", False):
            _, _, grouping = queryset.query.get_compiler(
                using="default"
            ).pre_sql_setup()
            self.assertEqual(len(grouping), len(Book._meta.fields) + 1)
            for index, field in enumerate(Book._meta.fields):
                self.assertIn(field.name, grouping[index][0])
            self.assertIn(Author._meta.pk.name, grouping[-1][0])
            assertQuerysetResults(queryset)
        # Unmanaged related model.
        with mock.patch.object(Author._meta, "managed", False):
            _, _, grouping = queryset.query.get_compiler(
                using="default"
            ).pre_sql_setup()
            self.assertEqual(len(grouping), len(Author._meta.fields) + 1)
            self.assertIn(Book._meta.pk.name, grouping[0][0])
            for index, field in enumerate(Author._meta.fields):
                self.assertIn(field.name, grouping[index + 1][0])
            assertQuerysetResults(queryset)