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