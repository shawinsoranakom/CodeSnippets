def test_forward_and_back(self):
        with self.assertNumQueries(1):
            stat = UserStat.objects.select_related("user__userprofile").get(
                user__username="test"
            )
            self.assertEqual(stat.user.userprofile.state, "KS")
            self.assertEqual(stat.user.userstat.posts, 150)