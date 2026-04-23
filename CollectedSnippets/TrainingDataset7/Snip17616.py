async def test_asuperuser(self):
        "Check the creation and properties of a superuser"
        super = await User.objects.acreate_superuser(
            "super", "super@example.com", "super"
        )
        self.assertTrue(super.is_superuser)
        self.assertTrue(super.is_active)
        self.assertTrue(super.is_staff)