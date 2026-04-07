def test_reverse_fk_update(self):
        owner = Person.objects.create(name="Someone")
        Pet.objects.create(name="fido", owner=owner)
        with self.assertRaises(RouterUsed) as cm:
            with self.override_router():
                owner.pet_set.update(name="max")
        e = cm.exception
        self.assertEqual(e.mode, RouterUsed.WRITE)
        self.assertEqual(e.model, Pet)
        self.assertEqual(e.hints, {"instance": owner})