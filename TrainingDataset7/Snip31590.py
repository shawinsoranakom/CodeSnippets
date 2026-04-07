def test_basic(self):
        with self.assertNumQueries(1):
            u = User.objects.select_related("userprofile").get(username="test")
            self.assertEqual(u.userprofile.state, "KS")