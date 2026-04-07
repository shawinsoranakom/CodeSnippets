def test_self_referential_non_symmetrical_both(self):
        tony = PersonSelfRefM2M.objects.create(name="Tony")
        chris = PersonSelfRefM2M.objects.create(name="Chris")
        Friendship.objects.create(
            first=tony, second=chris, date_friended=datetime.now()
        )
        Friendship.objects.create(
            first=chris, second=tony, date_friended=datetime.now()
        )

        self.assertQuerySetEqual(tony.friends.all(), ["Chris"], attrgetter("name"))

        self.assertQuerySetEqual(chris.friends.all(), ["Tony"], attrgetter("name"))