def test_reverse_fk_get_or_create(self):
        owner = Person.objects.create(name="Someone")
        with self.assertRaises(RouterUsed) as cm:
            with self.override_router():
                owner.pet_set.get_or_create(name="fido")
        e = cm.exception
        self.assertEqual(e.mode, RouterUsed.WRITE)
        self.assertEqual(e.model, Pet)
        self.assertEqual(e.hints, {"instance": owner})