def test_fast_delete_full_match(self):
        avatar = Avatar.objects.create(desc="bar")
        User.objects.create(avatar=avatar)
        with self.assertNumQueries(1):
            User.objects.filter(~Q(pk__in=[]) | Q(avatar__desc="foo")).delete()
        self.assertFalse(User.objects.exists())