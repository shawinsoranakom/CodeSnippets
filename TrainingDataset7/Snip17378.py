async def test_aauthenticate(self):
        user = await aauthenticate(username="testuser", password="testpw")
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, self.test_user.username)
        user.is_active = False
        await user.asave()
        self.assertIsNone(await aauthenticate(username="testuser", password="testpw"))