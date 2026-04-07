def test_not_followed_by_default(self):
        with self.assertNumQueries(2):
            u = User.objects.select_related().get(username="test")
            self.assertEqual(u.userstat.posts, 150)