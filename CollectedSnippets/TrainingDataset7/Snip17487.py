def test_add_view(self, mock):
        for db in self.databases:
            with self.subTest(db_connection=db):
                Router.target_db = db
                self.client.force_login(self.superusers[db])
                response = self.client.post(
                    reverse("test_adminsite:auth_user_add"),
                    {
                        "username": "some_user",
                        "password1": "helloworld",
                        "password2": "helloworld",
                    },
                )
                self.assertEqual(response.status_code, 302)
                mock.atomic.assert_called_with(using=db)