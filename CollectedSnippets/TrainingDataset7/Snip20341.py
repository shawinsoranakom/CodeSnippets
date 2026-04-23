def test_collate_filter_ci(self):
        collation = connection.features.test_collations.get("ci")
        if not collation:
            self.skipTest("This backend does not support case-insensitive collations.")
        qs = Author.objects.filter(alias=Collate(Value("a"), collation))
        self.assertEqual(qs.count(), 2)