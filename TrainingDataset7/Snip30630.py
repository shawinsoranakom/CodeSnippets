def test_ticket_10790_6(self):
        # Querying with isnull=True across m2m field should not create inner
        # joins and strip last outer join
        q = Author.objects.filter(item__tags__parent__parent__isnull=True)
        self.assertSequenceEqual(
            q,
            [self.a1, self.a1, self.a2, self.a2, self.a2, self.a3],
        )
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 4)
        self.assertEqual(str(q.query).count("INNER JOIN"), 0)

        q = Author.objects.filter(item__tags__parent__isnull=True)
        self.assertSequenceEqual(q, [self.a1, self.a2, self.a2, self.a3])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 3)
        self.assertEqual(str(q.query).count("INNER JOIN"), 0)