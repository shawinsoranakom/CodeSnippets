def test_lang_name_present(self):
        with translation.override(None):
            response = self.client.get(reverse("admin:app_list", args=("admin_views",)))
            self.assertNotContains(response, ' lang=""')
            self.assertNotContains(response, ' xml:lang=""')