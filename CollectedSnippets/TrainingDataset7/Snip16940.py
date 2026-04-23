def test_annotate_m2m(self):
        books = (
            Book.objects.filter(rating__lt=4.5)
            .annotate(Avg("authors__age"))
            .order_by("name")
        )
        self.assertQuerySetEqual(
            books,
            [
                ("Artificial Intelligence: A Modern Approach", 51.5),
                ("Practical Django Projects", 29.0),
                ("Python Web Development with Django", Approximate(30.3, places=1)),
                ("Sams Teach Yourself Django in 24 Hours", 45.0),
            ],
            lambda b: (b.name, b.authors__age__avg),
        )

        books = Book.objects.annotate(num_authors=Count("authors")).order_by("name")
        self.assertQuerySetEqual(
            books,
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
            lambda b: (b.name, b.num_authors),
        )