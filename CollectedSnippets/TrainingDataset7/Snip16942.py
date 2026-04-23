def test_reverse_fkey_annotate(self):
        books = Book.objects.annotate(Sum("publisher__num_awards")).order_by("name")
        self.assertQuerySetEqual(
            books,
            [
                ("Artificial Intelligence: A Modern Approach", 7),
                (
                    "Paradigms of Artificial Intelligence Programming: Case Studies in "
                    "Common Lisp",
                    9,
                ),
                ("Practical Django Projects", 3),
                ("Python Web Development with Django", 7),
                ("Sams Teach Yourself Django in 24 Hours", 1),
                ("The Definitive Guide to Django: Web Development Done Right", 3),
            ],
            lambda b: (b.name, b.publisher__num_awards__sum),
        )

        publishers = Publisher.objects.annotate(Sum("book__price")).order_by("name")
        self.assertQuerySetEqual(
            publishers,
            [
                ("Apress", Decimal("59.69")),
                ("Jonno's House of Books", None),
                ("Morgan Kaufmann", Decimal("75.00")),
                ("Prentice Hall", Decimal("112.49")),
                ("Sams", Decimal("23.09")),
            ],
            lambda p: (p.name, p.book__price__sum),
        )