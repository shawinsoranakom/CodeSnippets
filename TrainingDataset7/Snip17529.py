async def test_aauthenticate(self):
        test_user = await CustomUser._default_manager.acreate_user(
            email="test@example.com", password="test", date_of_birth=date(2006, 4, 25)
        )
        authenticated_user = await aauthenticate(
            email="test@example.com", password="test"
        )
        self.assertEqual(test_user, authenticated_user)