def test_cache_read_for_model_instance_with_deferred(self):
        # Don't want fields with callable as default to be called on cache read
        expensive_calculation.num_runs = 0
        Poll.objects.all().delete()
        Poll.objects.create(question="What?")
        self.assertEqual(expensive_calculation.num_runs, 1)
        defer_qs = Poll.objects.defer("question")
        self.assertEqual(defer_qs.count(), 1)
        cache.set("deferred_queryset", defer_qs)
        self.assertEqual(expensive_calculation.num_runs, 1)
        runs_before_cache_read = expensive_calculation.num_runs
        cache.get("deferred_queryset")
        # We only want the default expensive calculation run on creation and
        # set
        self.assertEqual(expensive_calculation.num_runs, runs_before_cache_read)