def test_order_by_group_by_join(self):
        # Regression for #10113 - Fields mentioned in order_by() must be
        # included in the GROUP BY. This only becomes a problem when the
        # order_by introduces a new join.
        self.assertQuerySetEqual(
            Book.objects.annotate(num_authors=Count("authors")).order_by(
                "publisher__name", "name"
            ),
            [
                "Practical Django Projects",
                "The Definitive Guide to Django: Web Development Done Right",
                "Paradigms of Artificial Intelligence Programming: Case Studies in "
                "Common Lisp",
                "Artificial Intelligence: A Modern Approach",
                "Python Web Development with Django",
                "Sams Teach Yourself Django in 24 Hours",
            ],
            lambda b: b.name,
        )