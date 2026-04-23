def test_cache_write_for_model_instance_with_deferred(self):
        # Don't want fields with callable as default to be called on cache
        # write
        expensive_calculation.num_runs = 0
        Poll.objects.all().delete()
        Poll.objects.create(question="What?")
        self.assertEqual(expensive_calculation.num_runs, 1)
        defer_qs = Poll.objects.defer("question")
        self.assertEqual(defer_qs.count(), 1)
        self.assertEqual(expensive_calculation.num_runs, 1)
        cache.set("deferred_queryset", defer_qs)
        # cache set should not re-evaluate default functions
        self.assertEqual(expensive_calculation.num_runs, 1)