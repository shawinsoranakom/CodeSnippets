def test_annotate_basic(self):
        self.assertQuerySetEqual(
            Book.objects.annotate().order_by("pk"),
            [
                "The Definitive Guide to Django: Web Development Done Right",
                "Sams Teach Yourself Django in 24 Hours",
                "Practical Django Projects",
                "Python Web Development with Django",
                "Artificial Intelligence: A Modern Approach",
                "Paradigms of Artificial Intelligence Programming: Case Studies in "
                "Common Lisp",
            ],
            lambda b: b.name,
        )

        books = Book.objects.annotate(mean_age=Avg("authors__age"))
        b = books.get(pk=self.b1.pk)
        self.assertEqual(
            b.name, "The Definitive Guide to Django: Web Development Done Right"
        )
        self.assertEqual(b.mean_age, 34.5)