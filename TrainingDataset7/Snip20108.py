def test_author_querying(self):
        self.assertSequenceEqual(
            Author.objects.order_by("last_name"),
            [self.a2, self.a1],
        )