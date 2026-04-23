async def test_aauthenticate(self):
        self.assertEqual(
            await aauthenticate(username="test", password="test"), self.user1
        )