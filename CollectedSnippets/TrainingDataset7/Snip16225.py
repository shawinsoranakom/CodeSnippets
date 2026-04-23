def test_contenttype_in_separate_db(self):
        ContentType.objects.using("other").all().delete()
        book = Book.objects.using("other").create(name="other book")
        user = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )

        book_type = ContentType.objects.get(app_label="admin_views", model="book")

        self.client.force_login(user)

        shortcut_url = reverse("admin:view_on_site", args=(book_type.pk, book.id))
        response = self.client.get(shortcut_url, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertRegex(
            response.url, f"http://(testserver|example.com)/books/{book.id}/"
        )