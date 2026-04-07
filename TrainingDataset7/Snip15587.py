def test_tabular_inline_delete_layout(self):
        from selenium.webdriver.common.by import By

        user = User.objects.create_user("testing", password="password", is_staff=True)
        et_permission = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(ExtraTerrestrial),
        )
        s_permission = Permission.objects.filter(
            codename__in=["view_sighting", "add_sighting"],
            content_type=ContentType.objects.get_for_model(Sighting),
        )
        user.user_permissions.add(*et_permission, *s_permission)
        self.admin_login(username="testing", password="password")
        cf = ExtraTerrestrial.objects.create(name="test")
        url = reverse("admin:admin_inlines_extraterrestrial_change", args=(cf.pk,))
        self.selenium.get(self.live_server_url + url)
        headers = self.selenium.find_elements(
            By.CSS_SELECTOR, "fieldset.module thead tr th"
        )
        self.assertHTMLEqual(headers[-1].get_attribute("outerHTML"), "<th></th>")
        delete = self.selenium.find_element(
            By.CSS_SELECTOR,
            "fieldset.module tbody tr.dynamic-sighting_set:not(.original) td.delete",
        )
        self.assertIn(
            '<a role="button" class="inline-deletelink" href="#">',
            delete.get_attribute("innerHTML"),
        )
        self.take_screenshot("loaded")