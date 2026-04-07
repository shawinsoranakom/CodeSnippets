async def test_aauthenticate_user_without_is_active_field(self):
        """
        A custom user without an `is_active` field is allowed to authenticate.
        """
        user = await CustomUserWithoutIsActiveField.objects._acreate_user(
            username="test",
            email="test@example.com",
            password="test",
        )
        self.assertEqual(await aauthenticate(username="test", password="test"), user)