def test_force_insert_false_with_existing_parent(self):
        parent = Counter.objects.create(pk=1, value=1)
        with self.assertNumQueries(2):
            SubCounter.objects.create(pk=parent.pk, value=2)