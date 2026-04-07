def test_reverse_fk_delete(self):
        owner = Person.objects.create(name="Someone")
        to_del_qs = owner.pet_set.all()
        with self.assertRaises(RouterUsed) as cm:
            with self.override_router():
                to_del_qs.delete()
        e = cm.exception
        self.assertEqual(e.mode, RouterUsed.WRITE)
        self.assertEqual(e.model, Pet)
        self.assertEqual(e.hints, {"instance": owner})