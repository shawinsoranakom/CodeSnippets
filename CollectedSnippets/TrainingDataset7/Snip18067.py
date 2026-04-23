async def test_user_after_alogout(self):
        await alogout(self.request)
        self.assertEqual(self.request.user, AnonymousUser())