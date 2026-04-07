async def test_aget_user_fallback_secret(self):
        created_user = await User.objects.acreate_user(
            "testuser", "test@example.com", "testpw"
        )
        await self.client.alogin(username="testuser", password="testpw")
        request = HttpRequest()
        request.session = await self.client.asession()
        prev_session_key = request.session.session_key
        with override_settings(
            SECRET_KEY="newsecret",
            SECRET_KEY_FALLBACKS=[settings.SECRET_KEY],
        ):
            user = await aget_user(request)
            self.assertIsInstance(user, User)
            self.assertEqual(user.username, created_user.username)
            self.assertNotEqual(request.session.session_key, prev_session_key)
        # Remove the fallback secret.
        # The session hash should be updated using the current secret.
        with override_settings(SECRET_KEY="newsecret"):
            user = await aget_user(request)
            self.assertIsInstance(user, User)
            self.assertEqual(user.username, created_user.username)