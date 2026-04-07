def test_ticket_10790_8(self):
        # Querying with combined q-objects should also strip the left outer
        # join
        q = Tag.objects.filter(Q(parent__isnull=True) | Q(parent=self.t1))
        self.assertSequenceEqual(q, [self.t1, self.t2, self.t3])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q.query).count("INNER JOIN"), 0)