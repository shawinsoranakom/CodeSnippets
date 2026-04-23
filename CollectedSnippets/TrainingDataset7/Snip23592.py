def test_extra_join_condition(self):
        # A crude check that content_type_id is taken in account in the
        # join/subquery condition.
        self.assertIn(
            "content_type_id", str(B.objects.exclude(a__flag=None).query).lower()
        )
        # No need for any joins - the join from inner query can be trimmed in
        # this case (but not in the above case as no a objects at all for given
        # B would then fail).
        self.assertNotIn(" join ", str(B.objects.exclude(a__flag=True).query).lower())
        self.assertIn(
            "content_type_id", str(B.objects.exclude(a__flag=True).query).lower()
        )