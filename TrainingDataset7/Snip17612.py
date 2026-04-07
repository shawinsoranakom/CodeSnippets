async def test_acreate(self):
        u = await User.objects.acreate_user("testuser", "test@example.com", "testpw")
        self.assertTrue(u.has_usable_password())
        self.assertFalse(await u.acheck_password("bad"))
        self.assertTrue(await u.acheck_password("testpw"))