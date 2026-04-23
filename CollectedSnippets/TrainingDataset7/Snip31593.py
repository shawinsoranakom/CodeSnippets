def test_follow_two_next_level(self):
        with self.assertNumQueries(1):
            u = User.objects.select_related(
                "userstat__results", "userstat__statdetails"
            ).get(username="test")
            self.assertEqual(u.userstat.results.results, "first results")
            self.assertEqual(u.userstat.statdetails.comments, 259)