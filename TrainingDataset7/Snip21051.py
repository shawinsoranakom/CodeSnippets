def test_only_not_clear_cached_relations(self):
        obj = Secondary.objects.only("first").get(pk=self.secondary.pk)
        with self.assertNumQueries(1):
            obj.primary_o2o
        obj.second  # Accessing a deferred field.
        with self.assertNumQueries(0):
            obj.primary_o2o