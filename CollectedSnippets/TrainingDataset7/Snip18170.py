def test_create_user(self):
        User.objects.create_user("JohnDoe")
        self.assertEqual(self.signals_count, 1)