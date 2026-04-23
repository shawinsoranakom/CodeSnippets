def test_aggregate_cloning(self):
        # Regression for #10199 - Aggregate calls clone the original query so
        # the original query can still be used
        books = Book.objects.all()
        books.aggregate(Avg("authors__age"))
        self.assertQuerySetEqual(
            books.all(),
            [
                "Artificial Intelligence: A Modern Approach",
                "Paradigms of Artificial Intelligence Programming: Case Studies in "
                "Common Lisp",
                "Practical Django Projects",
                "Python Web Development with Django",
                "Sams Teach Yourself Django in 24 Hours",
                "The Definitive Guide to Django: Web Development Done Right",
            ],
            lambda b: b.name,
        )