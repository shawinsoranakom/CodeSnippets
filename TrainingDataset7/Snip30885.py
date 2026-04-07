def test_values_no_promotion_for_existing(self):
        qs = Node.objects.filter(parent__parent__isnull=False)
        self.assertIn(" INNER JOIN ", str(qs.query))
        qs = qs.values("parent__parent__id")
        self.assertIn(" INNER JOIN ", str(qs.query))
        # Make sure there is a left outer join without the filter.
        qs = Node.objects.values("parent__parent__id")
        self.assertIn(" LEFT OUTER JOIN ", str(qs.query))