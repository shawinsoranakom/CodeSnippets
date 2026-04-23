def test_self_referential_symmetrical(self):
        tony = PersonSelfRefM2M.objects.create(name="Tony")
        chris = PersonSelfRefM2M.objects.create(name="Chris")
        SymmetricalFriendship.objects.create(
            first=tony,
            second=chris,
            date_friended=date.today(),
        )
        self.assertSequenceEqual(tony.sym_friends.all(), [chris])
        # Manually created symmetrical m2m relation doesn't add mirror entry
        # automatically.
        self.assertSequenceEqual(chris.sym_friends.all(), [])
        SymmetricalFriendship.objects.create(
            first=chris, second=tony, date_friended=date.today()
        )
        self.assertSequenceEqual(chris.sym_friends.all(), [tony])