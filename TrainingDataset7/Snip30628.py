def test_ticket_10790_4(self):
        # Querying across m2m field should not strip the m2m table from join.
        q = Author.objects.filter(item__tags__isnull=True)
        self.assertSequenceEqual(q, [self.a2, self.a3])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 2)
        self.assertNotIn("INNER JOIN", str(q.query))

        q = Author.objects.filter(item__tags__parent__isnull=True)
        self.assertSequenceEqual(q, [self.a1, self.a2, self.a2, self.a3])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 3)
        self.assertNotIn("INNER JOIN", str(q.query))