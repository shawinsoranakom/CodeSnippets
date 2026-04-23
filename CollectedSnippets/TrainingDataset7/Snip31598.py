def test_follow_inheritance(self):
        with self.assertNumQueries(1):
            stat = UserStat.objects.select_related("user", "advanceduserstat").get(
                posts=200
            )
            self.assertEqual(stat.advanceduserstat.posts, 200)
            self.assertEqual(stat.user.username, "bob")
        with self.assertNumQueries(0):
            self.assertEqual(stat.advanceduserstat.user.username, "bob")