def test_language_collation_order_by(self):
        collation = connection.features.test_collations.get("swedish_ci")
        if not collation:
            self.skipTest("This backend does not support language collations.")
        author3 = Author.objects.create(alias="O", name="Jones")
        author4 = Author.objects.create(alias="Ö", name="Jones")
        author5 = Author.objects.create(alias="P", name="Jones")
        qs = Author.objects.order_by(Collate(F("alias"), collation), "name")
        self.assertSequenceEqual(
            qs,
            [self.author1, self.author2, author3, author5, author4],
        )