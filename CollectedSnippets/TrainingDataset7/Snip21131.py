def test_fast_delete_fk(self):
        u = User.objects.create(avatar=Avatar.objects.create())
        a = Avatar.objects.get(pk=u.avatar_id)
        # 1 query to fast-delete the user
        # 1 query to delete the avatar
        self.assertNumQueries(2, a.delete)
        self.assertFalse(User.objects.exists())
        self.assertFalse(Avatar.objects.exists())