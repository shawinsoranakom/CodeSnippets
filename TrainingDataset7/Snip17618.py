def test_get_user_model(self):
        "The current user model can be retrieved"
        self.assertEqual(get_user_model(), User)