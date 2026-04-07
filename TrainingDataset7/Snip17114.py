def test_annotate_ordering_by_annotation_and_filtering(self):
        # Note: intentionally no order_by(), that case needs tests, too.
        publishers = Publisher.objects.filter(id__in=[self.p1.id, self.p2.id])
        self.assertEqual(sorted(p.name for p in publishers), ["Apress", "Sams"])

        publishers = publishers.annotate(n_books=Count("book"))
        sorted_publishers = sorted(publishers, key=lambda x: x.name)
        self.assertEqual(sorted_publishers[0].n_books, 2)
        self.assertEqual(sorted_publishers[1].n_books, 1)

        self.assertEqual(sorted(p.name for p in publishers), ["Apress", "Sams"])

        books = Book.objects.filter(publisher__in=publishers)
        self.assertQuerySetEqual(
            books,
            [
                "Practical Django Projects",
                "Sams Teach Yourself Django in 24 Hours",
                "The Definitive Guide to Django: Web Development Done Right",
            ],
            lambda b: b.name,
        )
        self.assertEqual(sorted(p.name for p in publishers), ["Apress", "Sams"])