def test_back_and_forward(self):
        with self.assertNumQueries(1):
            u = User.objects.select_related("userstat").get(username="test")
            self.assertEqual(u.userstat.user.username, "test")