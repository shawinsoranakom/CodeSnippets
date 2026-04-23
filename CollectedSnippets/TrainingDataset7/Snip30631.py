def test_ticket_10790_7(self):
        # Reverse querying with isnull should not strip the join
        q = Author.objects.filter(item__isnull=True)
        self.assertSequenceEqual(q, [self.a3])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 1)
        self.assertEqual(str(q.query).count("INNER JOIN"), 0)

        q = Author.objects.filter(item__isnull=False)
        self.assertSequenceEqual(q, [self.a1, self.a2, self.a2, self.a4])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q.query).count("INNER JOIN"), 1)