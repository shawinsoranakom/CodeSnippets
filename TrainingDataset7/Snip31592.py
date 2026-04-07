def test_follow_two(self):
        with self.assertNumQueries(1):
            u = User.objects.select_related("userprofile", "userstat").get(
                username="test"
            )
            self.assertEqual(u.userprofile.state, "KS")
            self.assertEqual(u.userstat.posts, 150)