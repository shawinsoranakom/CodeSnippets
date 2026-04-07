async def test_user_after_alogin(self):
        await alogin(self.request, self.user2)
        self.assertEqual(self.request.user, self.user2)