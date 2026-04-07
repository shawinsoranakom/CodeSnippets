def county_helper(self, county_feat=True):
        """
        Helper function for ensuring the integrity of the mapped County models.
        """
        for name, n, st in zip(NAMES, NUMS, STATES):
            # Should only be one record b/c of `unique` keyword.
            c = County.objects.get(name=name)
            self.assertEqual(n, len(c.mpoly))
            self.assertEqual(st, c.state.name)  # Checking ForeignKey mapping.

            # Multiple records because `unique` was not set.
            if county_feat:
                qs = CountyFeat.objects.filter(name=name)
                self.assertEqual(n, qs.count())