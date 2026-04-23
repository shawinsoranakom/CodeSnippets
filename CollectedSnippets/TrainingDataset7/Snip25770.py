def test_in_bulk_preserve_ordering(self):
        self.assertEqual(
            list(Article.objects.in_bulk([self.a2.id, self.a1.id])),
            [self.a2.id, self.a1.id],
        )