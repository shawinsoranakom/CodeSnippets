def test_ticket_24748(self):
        t1 = SelfRefFK.objects.create(name="t1")
        SelfRefFK.objects.create(name="t2", parent=t1)
        SelfRefFK.objects.create(name="t3", parent=t1)
        self.assertQuerySetEqual(
            SelfRefFK.objects.annotate(num_children=Count("children")).order_by("name"),
            [("t1", 2), ("t2", 0), ("t3", 0)],
            lambda x: (x.name, x.num_children),
        )