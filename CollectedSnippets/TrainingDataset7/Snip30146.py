def test_m2m_forward(self):
        with self.assertNumQueries(2):
            lists = [
                list(b.authors.all()) for b in Book.objects.prefetch_related("authors")
            ]

        normal_lists = [list(b.authors.all()) for b in Book.objects.all()]
        self.assertEqual(lists, normal_lists)