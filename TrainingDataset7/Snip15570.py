def test_fieldset_context_fully_set(self):
        url = reverse("admin:admin_inlines_photographer_add")
        with self.assertRaisesMessage(AssertionError, "no logs"):
            with self.assertLogs("django.template", "DEBUG"):
                self.client.get(url)