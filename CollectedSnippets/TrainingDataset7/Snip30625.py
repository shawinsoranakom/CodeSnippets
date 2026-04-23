def test_ticket_10790_1(self):
        # Querying direct fields with isnull should trim the left outer join.
        # It also should not create INNER JOIN.
        q = Tag.objects.filter(parent__isnull=True)

        self.assertSequenceEqual(q, [self.t1])
        self.assertNotIn("JOIN", str(q.query))

        q = Tag.objects.filter(parent__isnull=False)

        self.assertSequenceEqual(q, [self.t2, self.t3, self.t4, self.t5])
        self.assertNotIn("JOIN", str(q.query))

        q = Tag.objects.exclude(parent__isnull=True)
        self.assertSequenceEqual(q, [self.t2, self.t3, self.t4, self.t5])
        self.assertNotIn("JOIN", str(q.query))

        q = Tag.objects.exclude(parent__isnull=False)
        self.assertSequenceEqual(q, [self.t1])
        self.assertNotIn("JOIN", str(q.query))

        q = Tag.objects.exclude(parent__parent__isnull=False)

        self.assertSequenceEqual(q, [self.t1, self.t2, self.t3])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 1)
        self.assertNotIn("INNER JOIN", str(q.query))