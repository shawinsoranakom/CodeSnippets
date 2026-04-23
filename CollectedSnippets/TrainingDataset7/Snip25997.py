def test_self_referential_empty_qs(self):
        tony = PersonSelfRefM2M.objects.create(name="Tony")
        self.assertQuerySetEqual(tony.friends.all(), [])