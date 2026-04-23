def test_superuser(self):
        "Check the creation and properties of a superuser"
        super = User.objects.create_superuser("super", "super@example.com", "super")
        self.assertTrue(super.is_superuser)
        self.assertTrue(super.is_active)
        self.assertTrue(super.is_staff)