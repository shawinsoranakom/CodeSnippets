def test_fast_delete_empty_result_set(self):
        user = User.objects.create()
        with self.assertNumQueries(0):
            self.assertEqual(
                User.objects.filter(pk__in=[]).delete(),
                (0, {}),
            )
        self.assertSequenceEqual(User.objects.all(), [user])