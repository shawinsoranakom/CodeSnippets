def test_use_fieldset_fields_render(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        course = Course.objects.create(
            title="Django Class", materials="django_documents"
        )
        expected_legend_tags_text = [
            "Difficulty:",
            "Materials:",
            "Start datetime:",
        ]
        url = reverse("admin:admin_views_course_change", args=(course.pk,))
        self.selenium.get(self.live_server_url + url)
        fieldsets = self.selenium.find_elements(
            By.CSS_SELECTOR, "fieldset.aligned fieldset"
        )
        self.assertEqual(len(fieldsets), len(expected_legend_tags_text))
        for index, fieldset in enumerate(fieldsets):
            legend = fieldset.find_element(By.TAG_NAME, "legend")
            self.assertEqual(legend.text, expected_legend_tags_text[index])

        # FilteredSelectMultiple uses <fieldset>.
        url = reverse("admin:admin_views_camelcaserelatedmodel_add")
        self.selenium.get(self.live_server_url + url)
        fieldsets = self.selenium.find_elements(
            By.CSS_SELECTOR, "fieldset.aligned fieldset"
        )
        self.assertEqual(len(fieldsets), 1)
        for index, fieldset in enumerate(fieldsets):
            legend = fieldset.find_element(By.TAG_NAME, "legend")
            self.assertEqual(legend.text, "M2m:")