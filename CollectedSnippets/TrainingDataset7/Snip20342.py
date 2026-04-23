def test_collate_order_by_cs(self):
        collation = connection.features.test_collations.get("cs")
        if not collation:
            self.skipTest("This backend does not support case-sensitive collations.")
        qs = Author.objects.order_by(Collate("alias", collation))
        self.assertSequenceEqual(qs, [self.author2, self.author1])