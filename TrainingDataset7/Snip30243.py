def setUpTestData(cls):
        cls.rooms = []
        for _ in range(3):
            house = House.objects.create()
            for _ in range(3):
                cls.rooms.append(Room.objects.create(house=house))
            # Set main_room for each house before creating the next one for
            # databases where supports_nullable_unique_constraints is False.
            house.main_room = cls.rooms[-3]
            house.save()