def test_eq(self):
        self.assertEqual(self.user, AnonymousUser())
        self.assertNotEqual(self.user, User("super", "super@example.com", "super"))