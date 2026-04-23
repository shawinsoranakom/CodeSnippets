def test_add_on_symmetrical_m2m_with_intermediate_model(self):
        tony = PersonSelfRefM2M.objects.create(name="Tony")
        chris = PersonSelfRefM2M.objects.create(name="Chris")
        date_friended = date(2017, 1, 3)
        tony.sym_friends.add(chris, through_defaults={"date_friended": date_friended})
        self.assertSequenceEqual(tony.sym_friends.all(), [chris])
        self.assertSequenceEqual(chris.sym_friends.all(), [tony])
        friendship = tony.symmetricalfriendship_set.get()
        self.assertEqual(friendship.date_friended, date_friended)