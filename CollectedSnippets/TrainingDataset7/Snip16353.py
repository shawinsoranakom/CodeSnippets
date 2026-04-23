def test_password_change_helptext(self):
        response = self.client.get(reverse("admin:password_change"))
        self.assertContains(
            response, '<div class="help" id="id_new_password1_helptext">'
        )