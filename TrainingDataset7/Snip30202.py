def test_to_attr_doesnt_cache_through_attr_as_list(self):
        house = House.objects.prefetch_related(
            Prefetch("rooms", queryset=Room.objects.all(), to_attr="to_rooms"),
        ).get(pk=self.house3.pk)
        self.assertIsInstance(house.rooms.all(), QuerySet)