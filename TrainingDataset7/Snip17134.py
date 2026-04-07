def test_aggregate_unmanaged_model_as_tables(self):
        qs = Book.objects.select_related("contact").annotate(
            num_authors=Count("authors")
        )
        # Force treating unmanaged models as tables.
        with mock.patch(
            "django.db.connection.features.allows_group_by_selected_pks_on_model",
            return_value=True,
        ):
            with (
                mock.patch.object(Book._meta, "managed", False),
                mock.patch.object(Author._meta, "managed", False),
            ):
                _, _, grouping = qs.query.get_compiler(using="default").pre_sql_setup()
                self.assertEqual(len(grouping), 2)
                self.assertIn("id", grouping[0][0])
                self.assertIn("id", grouping[1][0])
                self.assertQuerySetEqual(
                    qs.order_by("name"),
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
                        (
                            "The Definitive Guide to Django: Web Development Done "
                            "Right",
                            2,
                        ),
                    ],
                    attrgetter("name", "num_authors"),
                )