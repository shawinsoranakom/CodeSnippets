def setUpTestData(cls):
        person1 = Person.objects.create(name="Joe")
        person2 = Person.objects.create(name="Mary")

        # Set main_room for each house before creating the next one for
        # databases where supports_nullable_unique_constraints is False.
        house1 = House.objects.create(address="123 Main St")
        room1_1 = Room.objects.create(name="Dining room", house=house1)
        Room.objects.create(name="Lounge", house=house1)
        Room.objects.create(name="Kitchen", house=house1)
        house1.main_room = room1_1
        house1.save()
        person1.houses.add(house1)

        house2 = House.objects.create(address="45 Side St")
        room2_1 = Room.objects.create(name="Dining room", house=house2)
        Room.objects.create(name="Lounge", house=house2)
        house2.main_room = room2_1
        house2.save()
        person1.houses.add(house2)

        house3 = House.objects.create(address="6 Downing St")
        room3_1 = Room.objects.create(name="Dining room", house=house3)
        Room.objects.create(name="Lounge", house=house3)
        Room.objects.create(name="Kitchen", house=house3)
        house3.main_room = room3_1
        house3.save()
        person2.houses.add(house3)

        house4 = House.objects.create(address="7 Regents St")
        room4_1 = Room.objects.create(name="Dining room", house=house4)
        Room.objects.create(name="Lounge", house=house4)
        house4.main_room = room4_1
        house4.save()
        person2.houses.add(house4)