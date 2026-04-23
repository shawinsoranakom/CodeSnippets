def test_fast_delete_joined_qs(self):
        a = Avatar.objects.create(desc="a")
        User.objects.create(avatar=a)
        u2 = User.objects.create()
        self.assertNumQueries(1, User.objects.filter(avatar__desc="a").delete)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(pk=u2.pk).exists())