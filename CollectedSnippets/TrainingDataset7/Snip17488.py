def test_read_only_methods_add_view(self, mock):
        for db in self.databases:
            for method in self.READ_ONLY_METHODS:
                with self.subTest(db_connection=db, method=method):
                    mock.mock_reset()
                    Router.target_db = db
                    self.client.force_login(self.superusers[db])
                    response = getattr(self.client, method)(
                        reverse("test_adminsite:auth_user_add")
                    )
                    self.assertEqual(response.status_code, 200)
                    mock.atomic.assert_not_called()