def test_skips_backends_with_decorated_method(self):
        self.assertEqual(authenticate(username="test", password="test"), self.user1)