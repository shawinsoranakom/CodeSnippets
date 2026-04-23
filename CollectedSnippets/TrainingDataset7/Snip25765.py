def test_in_bulk(self):
        # in_bulk() takes a list of IDs and returns a dictionary mapping IDs to
        # objects.
        arts = Article.objects.in_bulk([self.a1.id, self.a2.id])
        self.assertEqual(arts[self.a1.id], self.a1)
        self.assertEqual(arts[self.a2.id], self.a2)
        self.assertEqual(
            Article.objects.in_bulk(),
            {
                self.a1.id: self.a1,
                self.a2.id: self.a2,
                self.a3.id: self.a3,
                self.a4.id: self.a4,
                self.a5.id: self.a5,
                self.a6.id: self.a6,
                self.a7.id: self.a7,
            },
        )
        self.assertEqual(Article.objects.in_bulk([self.a3.id]), {self.a3.id: self.a3})
        self.assertEqual(Article.objects.in_bulk({self.a3.id}), {self.a3.id: self.a3})
        self.assertEqual(
            Article.objects.in_bulk(frozenset([self.a3.id])), {self.a3.id: self.a3}
        )
        self.assertEqual(Article.objects.in_bulk((self.a3.id,)), {self.a3.id: self.a3})
        self.assertEqual(Article.objects.in_bulk([1000]), {})
        self.assertEqual(Article.objects.in_bulk([]), {})
        self.assertEqual(
            Article.objects.in_bulk(iter([self.a1.id])), {self.a1.id: self.a1}
        )
        self.assertEqual(Article.objects.in_bulk(iter([])), {})
        with self.assertRaises(TypeError):
            Article.objects.in_bulk(headline__startswith="Blah")