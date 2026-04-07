def test_get_random_secret_key(self):
        key = get_random_secret_key()
        self.assertEqual(len(key), 50)
        for char in key:
            self.assertIn(char, "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)")