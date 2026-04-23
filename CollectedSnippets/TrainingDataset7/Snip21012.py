def test_only_related_manager_optimization(self):
        s = Secondary.objects.create(first="one", second="two")
        Primary.objects.bulk_create(
            [Primary(name="p1", value="v1", related=s) for _ in range(5)]
        )
        with self.assertNumQueries(1):
            for p in s.primary_set.only("pk"):
                _ = p.pk