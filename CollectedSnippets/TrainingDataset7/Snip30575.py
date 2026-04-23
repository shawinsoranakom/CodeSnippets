def test_order_by_join_unref(self):
        """
        This test is related to the above one, testing that there aren't
        old JOINs in the query.
        """
        qs = Celebrity.objects.order_by("greatest_fan__fan_of")
        self.assertIn("OUTER JOIN", str(qs.query))
        qs = qs.order_by("id")
        self.assertNotIn("OUTER JOIN", str(qs.query))