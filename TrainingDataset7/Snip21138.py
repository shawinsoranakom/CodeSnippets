def test_fast_delete_large_batch(self):
        User.objects.bulk_create(User() for i in range(0, 2000))
        # No problems here - we aren't going to cascade, so we will fast
        # delete the objects in a single query.
        self.assertNumQueries(1, User.objects.all().delete)
        a = Avatar.objects.create(desc="a")
        User.objects.bulk_create(User(avatar=a) for i in range(0, 2000))
        # We don't hit parameter amount limits for a, so just one query for
        # that + fast delete of the related objs.
        self.assertNumQueries(2, a.delete)
        self.assertEqual(User.objects.count(), 0)