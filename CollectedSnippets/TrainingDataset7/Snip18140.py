async def test_acreate_superuser_raises_error_on_false_is_staff(self):
        with self.assertRaisesMessage(ValueError, "Superuser must have is_staff=True."):
            await User.objects.acreate_superuser(
                username="test",
                email="test@test.com",
                password="test",
                is_staff=False,
            )