def test_foreignkey_collection(self):
        person = Person.objects.create(name="Bob")
        Pet.objects.create(owner=person, name="Wart")
        # test related FK collection
        person.delete()