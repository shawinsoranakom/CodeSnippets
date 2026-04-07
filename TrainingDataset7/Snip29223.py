def test_reverse_one_to_one_relation(self):
        user = User(username="Someone", password="fake_hash")
        profile = UserProfile()
        with self.assertRaisesMessage(ValueError, self.router_prevents_msg):
            user.userprofile = profile