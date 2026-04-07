def test_hidden_related(self):
        r = R.objects.create()
        h = HiddenUser.objects.create(r=r)
        HiddenUserProfile.objects.create(user=h)

        r.delete()
        self.assertEqual(HiddenUserProfile.objects.count(), 0)