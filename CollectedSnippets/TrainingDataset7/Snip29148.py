def test_foreign_key_deletion(self):
        """
        Cascaded deletions of Foreign Key relations issue queries on the right
        database.
        """
        mark = Person.objects.using("other").create(name="Mark Pilgrim")
        Pet.objects.using("other").create(name="Fido", owner=mark)

        # Check the initial state
        self.assertEqual(Person.objects.using("default").count(), 0)
        self.assertEqual(Pet.objects.using("default").count(), 0)

        self.assertEqual(Person.objects.using("other").count(), 1)
        self.assertEqual(Pet.objects.using("other").count(), 1)

        # Delete the person object, which will cascade onto the pet
        mark.delete(using="other")

        self.assertEqual(Person.objects.using("default").count(), 0)
        self.assertEqual(Pet.objects.using("default").count(), 0)

        # Both the pet and the person have been deleted from the right database
        self.assertEqual(Person.objects.using("other").count(), 0)
        self.assertEqual(Pet.objects.using("other").count(), 0)