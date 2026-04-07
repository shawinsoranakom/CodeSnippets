def test_authenticate(self):
        test_user = CustomUser._default_manager.create_user(
            email="test@example.com", password="test", date_of_birth=date(2006, 4, 25)
        )
        authenticated_user = authenticate(email="test@example.com", password="test")
        self.assertEqual(test_user, authenticated_user)