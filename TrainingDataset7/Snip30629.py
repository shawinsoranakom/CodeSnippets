def test_ticket_10790_5(self):
        # Querying with isnull=False across m2m field should not create outer
        # joins
        q = Author.objects.filter(item__tags__isnull=False)
        self.assertSequenceEqual(q, [self.a1, self.a1, self.a2, self.a2, self.a4])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q.query).count("INNER JOIN"), 2)

        q = Author.objects.filter(item__tags__parent__isnull=False)
        self.assertSequenceEqual(q, [self.a1, self.a2, self.a4])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q.query).count("INNER JOIN"), 3)

        q = Author.objects.filter(item__tags__parent__parent__isnull=False)
        self.assertSequenceEqual(q, [self.a4])
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(q.query).count("INNER JOIN"), 4)