def test_ticket_10790_combine(self):
        # Combining queries should not re-populate the left outer join
        q1 = Tag.objects.filter(parent__isnull=True)
        q2 = Tag.objects.filter(parent__isnull=False)

        q3 = q1 | q2
        self.assertSequenceEqual(q3, [self.t1, self.t2, self.t3, self.t4, self.t5])
        self.assertEqual(str(q3.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q3.query).count("INNER JOIN"), 0)

        q3 = q1 & q2
        self.assertSequenceEqual(q3, [])
        self.assertEqual(str(q3.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q3.query).count("INNER JOIN"), 0)

        q2 = Tag.objects.filter(parent=self.t1)
        q3 = q1 | q2
        self.assertSequenceEqual(q3, [self.t1, self.t2, self.t3])
        self.assertEqual(str(q3.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q3.query).count("INNER JOIN"), 0)

        q3 = q2 | q1
        self.assertSequenceEqual(q3, [self.t1, self.t2, self.t3])
        self.assertEqual(str(q3.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q3.query).count("INNER JOIN"), 0)

        q1 = Tag.objects.filter(parent__isnull=True)
        q2 = Tag.objects.filter(parent__parent__isnull=True)

        q3 = q1 | q2
        self.assertSequenceEqual(q3, [self.t1, self.t2, self.t3])
        self.assertEqual(str(q3.query).count("LEFT OUTER JOIN"), 1)
        self.assertEqual(str(q3.query).count("INNER JOIN"), 0)

        q3 = q2 | q1
        self.assertSequenceEqual(q3, [self.t1, self.t2, self.t3])
        self.assertEqual(str(q3.query).count("LEFT OUTER JOIN"), 1)
        self.assertEqual(str(q3.query).count("INNER JOIN"), 0)