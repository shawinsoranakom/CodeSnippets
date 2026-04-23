def setUpTestData(cls):
        cls.person1 = Person.objects.create(name="Joe")
        cls.person2 = Person.objects.create(name="Mary")

        # Set main_room for each house before creating the next one for
        # databases where supports_nullable_unique_constraints is False.

        cls.house1 = House.objects.create(
            name="House 1", address="123 Main St", owner=cls.person1
        )
        cls.room1_1 = Room.objects.create(name="Dining room", house=cls.house1)
        cls.room1_2 = Room.objects.create(name="Lounge", house=cls.house1)
        cls.room1_3 = Room.objects.create(name="Kitchen", house=cls.house1)
        cls.house1.main_room = cls.room1_1
        cls.house1.save()
        cls.person1.houses.add(cls.house1)

        cls.house2 = House.objects.create(
            name="House 2", address="45 Side St", owner=cls.person1
        )
        cls.room2_1 = Room.objects.create(name="Dining room", house=cls.house2)
        cls.room2_2 = Room.objects.create(name="Lounge", house=cls.house2)
        cls.room2_3 = Room.objects.create(name="Kitchen", house=cls.house2)
        cls.house2.main_room = cls.room2_1
        cls.house2.save()
        cls.person1.houses.add(cls.house2)

        cls.house3 = House.objects.create(
            name="House 3", address="6 Downing St", owner=cls.person2
        )
        cls.room3_1 = Room.objects.create(name="Dining room", house=cls.house3)
        cls.room3_2 = Room.objects.create(name="Lounge", house=cls.house3)
        cls.room3_3 = Room.objects.create(name="Kitchen", house=cls.house3)
        cls.house3.main_room = cls.room3_1
        cls.house3.save()
        cls.person2.houses.add(cls.house3)

        cls.house4 = House.objects.create(
            name="house 4", address="7 Regents St", owner=cls.person2
        )
        cls.room4_1 = Room.objects.create(name="Dining room", house=cls.house4)
        cls.room4_2 = Room.objects.create(name="Lounge", house=cls.house4)
        cls.room4_3 = Room.objects.create(name="Kitchen", house=cls.house4)
        cls.house4.main_room = cls.room4_1
        cls.house4.save()
        cls.person2.houses.add(cls.house4)