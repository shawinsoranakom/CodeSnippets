def test_protected_view_logged_in_performance(self):
        """
        Protected views do trigger fetching the user from the database.
        """
        self.client.force_login(self.user)
        with self.assertNumQueries(2):  # session and user
            response = self.client.get("/protected_view/")
        self.assertEqual(response.status_code, 200)