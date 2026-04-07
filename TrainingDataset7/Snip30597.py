def test_ticket6154(self):
        # Multiple filter statements are joined using "AND" all the time.

        self.assertSequenceEqual(
            Author.objects.filter(id=self.a1.id).filter(
                Q(extra__note=self.n1) | Q(item__note=self.n3)
            ),
            [self.a1],
        )
        self.assertSequenceEqual(
            Author.objects.filter(
                Q(extra__note=self.n1) | Q(item__note=self.n3)
            ).filter(id=self.a1.id),
            [self.a1],
        )