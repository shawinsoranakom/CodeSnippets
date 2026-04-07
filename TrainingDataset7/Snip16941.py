def test_backwards_m2m_annotate(self):
        authors = (
            Author.objects.filter(name__contains="a")
            .annotate(Avg("book__rating"))
            .order_by("name")
        )
        self.assertQuerySetEqual(
            authors,
            [
                ("Adrian Holovaty", 4.5),
                ("Brad Dayley", 3.0),
                ("Jacob Kaplan-Moss", 4.5),
                ("James Bennett", 4.0),
                ("Paul Bissex", 4.0),
                ("Stuart Russell", 4.0),
            ],
            lambda a: (a.name, a.book__rating__avg),
        )

        authors = Author.objects.annotate(num_books=Count("book")).order_by("name")
        self.assertQuerySetEqual(
            authors,
            [
                ("Adrian Holovaty", 1),
                ("Brad Dayley", 1),
                ("Jacob Kaplan-Moss", 1),
                ("James Bennett", 1),
                ("Jeffrey Forcier", 1),
                ("Paul Bissex", 1),
                ("Peter Norvig", 2),
                ("Stuart Russell", 1),
                ("Wesley J. Chun", 1),
            ],
            lambda a: (a.name, a.num_books),
        )