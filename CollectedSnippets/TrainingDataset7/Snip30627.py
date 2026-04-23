def test_ticket_10790_3(self):
        # Querying via indirect fields should populate the left outer join
        q = NamedCategory.objects.filter(tag__isnull=True)
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 1)
        # join to dumbcategory ptr_id
        self.assertEqual(str(q.query).count("INNER JOIN"), 1)
        self.assertSequenceEqual(q, [])

        # Querying across several tables should strip only the last join, while
        # preserving the preceding left outer joins.
        q = NamedCategory.objects.filter(tag__parent__isnull=True)
        self.assertEqual(str(q.query).count("INNER JOIN"), 1)
        self.assertEqual(str(q.query).count("LEFT OUTER JOIN"), 1)
        self.assertSequenceEqual(q, [self.nc1])