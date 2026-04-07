def test_follow_from_child_class(self):
        with self.assertNumQueries(1):
            stat = AdvancedUserStat.objects.select_related("user", "statdetails").get(
                posts=200
            )
            self.assertEqual(stat.statdetails.comments, 250)
            self.assertEqual(stat.user.username, "bob")