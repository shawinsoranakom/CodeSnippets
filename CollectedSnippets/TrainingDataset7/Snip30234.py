def test_in_bulk(self):
        """
        In-bulk does correctly prefetch objects by not using .iterator()
        directly.
        """
        boss1 = Employee.objects.create(name="Peter")
        boss2 = Employee.objects.create(name="Jack")
        with self.assertNumQueries(2):
            # Prefetch is done and it does not cause any errors.
            bulk = Employee.objects.prefetch_related("serfs").in_bulk(
                [boss1.pk, boss2.pk]
            )
            for b in bulk.values():
                list(b.serfs.all())