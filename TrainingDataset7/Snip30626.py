def test_ticket_10790_2(self):
        # Querying across several tables should strip only the last outer join,
        # while preserving the preceding inner joins.
        q = Tag.objects.filter(parent__parent__isnull=False)

        self.assertSequenceEqual(q, [self.t4, self.t5])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q.query).count("INNER JOIN"), 1)

        # Querying without isnull should not convert anything to left outer
        # join.
        q = Tag.objects.filter(parent__parent=self.t1)
        self.assertSequenceEqual(q, [self.t4, self.t5])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q.query).count("INNER JOIN"), 1)