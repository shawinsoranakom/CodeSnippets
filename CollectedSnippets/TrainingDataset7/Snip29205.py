def test_fk_delete(self):
        owner = Person.objects.create(name="Someone")
        pet = Pet.objects.create(name="fido", owner=owner)
        with self.assertRaises(RouterUsed) as cm:
            with self.override_router():
                pet.owner.delete()
        e = cm.exception
        self.assertEqual(e.mode, RouterUsed.WRITE)
        self.assertEqual(e.model, Person)
        self.assertEqual(e.hints, {"instance": owner})