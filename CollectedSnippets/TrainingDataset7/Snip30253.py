def setUpTestData(cls):
        house = House.objects.create(name="Big house", address="123 Main St")
        cls.room = Room.objects.create(name="Kitchen", house=house)