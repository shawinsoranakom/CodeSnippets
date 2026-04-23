def logout(self):
        response = self.client.post("/admin/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)