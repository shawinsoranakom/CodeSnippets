def setUpTestData(cls):
        house = House.objects.create(name="Redwood", address="Arcata")
        room = Room.objects.create(name="Racoon", house=house)
        fleas = [Flea.objects.create(current_room=room) for i in range(3)]
        pet = Pet.objects.create(name="Spooky")
        pet.fleas_hosted.add(*fleas)
        person = Person.objects.create(name="Bob")
        person.houses.add(house)
        person.pets.add(pet)
        person.fleas_hosted.add(*fleas)