def test_add_view(self, mock):
        for db in self.databases:
            with self.subTest(db=db):
                mock.mock_reset()
                Router.target_db = db
                self.client.force_login(self.superusers[db])
                response = self.client.post(
                    reverse("test_adminsite:admin_views_book_add"),
                    {"name": "Foobar: 5th edition"},
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url, reverse("test_adminsite:admin_views_book_changelist")
                )
                mock.atomic.assert_called_with(using=db)