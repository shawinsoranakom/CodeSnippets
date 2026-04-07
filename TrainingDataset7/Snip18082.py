def test_public_view_logged_in_performance(self):
        """
        Public views don't trigger fetching the user from the database.
        """
        self.client.force_login(self.user)
        with self.assertNumQueries(0):
            response = self.client.get("/public_view/")
        self.assertEqual(response.status_code, 200)