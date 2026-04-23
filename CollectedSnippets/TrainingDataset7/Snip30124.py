def test_one_to_one_reverse(self):
        rooms = list(Room.objects.all())
        with self.assertNumQueries(1) as ctx:
            prefetch_related_objects(rooms, "main_room_of")
        self.assertNotIn("ORDER BY", ctx.captured_queries[0]["sql"])

        with self.assertNumQueries(0):
            [room.main_room_of for room in rooms]

        rooms = list(Room.objects.all())
        with self.assertNumQueries(1) as ctx:
            prefetch_related_objects(
                rooms,
                Prefetch("main_room_of", queryset=House.objects.order_by("-name")),
            )
        self.assertNotIn("ORDER BY", ctx.captured_queries[0]["sql"])