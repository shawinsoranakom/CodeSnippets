def test_one_to_one_forward(self):
        houses = list(House.objects.all())
        with self.assertNumQueries(1) as ctx:
            prefetch_related_objects(houses, "main_room")
        self.assertNotIn("ORDER BY", ctx.captured_queries[0]["sql"])

        with self.assertNumQueries(0):
            [house.main_room for house in houses]

        houses = list(House.objects.all())
        with self.assertNumQueries(1) as ctx:
            prefetch_related_objects(
                houses,
                Prefetch("main_room", queryset=Room.objects.order_by("-name")),
            )
        self.assertNotIn("ORDER BY", ctx.captured_queries[0]["sql"])