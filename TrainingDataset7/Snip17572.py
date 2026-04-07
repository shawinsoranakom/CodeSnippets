def test_authenticates(self):
        self.assertEqual(authenticate(username="test", password="test"), self.user1)