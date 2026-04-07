def test_set_on_symmetrical_m2m_with_intermediate_model(self):
        tony = PersonSelfRefM2M.objects.create(name="Tony")
        chris = PersonSelfRefM2M.objects.create(name="Chris")
        anne = PersonSelfRefM2M.objects.create(name="Anne")
        kate = PersonSelfRefM2M.objects.create(name="Kate")
        date_friended_add = date(2013, 1, 5)
        date_friended_set = date.today()
        tony.sym_friends.add(
            anne,
            chris,
            through_defaults={"date_friended": date_friended_add},
        )
        tony.sym_friends.set(
            [anne, kate],
            through_defaults={"date_friended": date_friended_set},
        )
        self.assertSequenceEqual(tony.sym_friends.all(), [anne, kate])
        self.assertSequenceEqual(anne.sym_friends.all(), [tony])
        self.assertSequenceEqual(kate.sym_friends.all(), [tony])
        self.assertEqual(
            kate.symmetricalfriendship_set.get().date_friended,
            date_friended_set,
        )
        # Date is preserved.
        self.assertEqual(
            anne.symmetricalfriendship_set.get().date_friended,
            date_friended_add,
        )
        # Recreate relationship.
        tony.sym_friends.set(
            [anne],
            clear=True,
            through_defaults={"date_friended": date_friended_set},
        )
        self.assertSequenceEqual(tony.sym_friends.all(), [anne])
        self.assertSequenceEqual(anne.sym_friends.all(), [tony])
        self.assertEqual(
            anne.symmetricalfriendship_set.get().date_friended,
            date_friended_set,
        )