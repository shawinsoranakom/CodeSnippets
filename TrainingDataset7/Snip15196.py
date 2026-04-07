def test_select_all_across_pages(self):
        from selenium.webdriver.common.by import By

        Parent.objects.bulk_create([Parent(name="parent%d" % i) for i in range(101)])
        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_changelist_parent_changelist")
        )

        selection_indicator = self.selenium.find_element(
            By.CSS_SELECTOR, ".action-counter"
        )
        select_all_indicator = self.selenium.find_element(
            By.CSS_SELECTOR, ".actions .all"
        )
        question = self.selenium.find_element(By.CSS_SELECTOR, ".actions > .question")
        clear = self.selenium.find_element(By.CSS_SELECTOR, ".actions > .clear")
        select_all = self.selenium.find_element(By.ID, "action-toggle")
        select_across = self.selenium.find_elements(By.NAME, "select_across")

        self.assertIs(question.is_displayed(), False)
        self.assertIs(clear.is_displayed(), False)
        self.assertIs(select_all.get_property("checked"), False)
        for hidden_input in select_across:
            self.assertEqual(hidden_input.get_property("value"), "0")
        self.assertIs(selection_indicator.is_displayed(), True)
        self.assertEqual(selection_indicator.text, "0 of 100 selected")
        self.assertIs(select_all_indicator.is_displayed(), False)

        select_all.click()
        self.assertIs(question.is_displayed(), True)
        self.assertIs(clear.is_displayed(), False)
        self.assertIs(select_all.get_property("checked"), True)
        for hidden_input in select_across:
            self.assertEqual(hidden_input.get_property("value"), "0")
        self.assertIs(selection_indicator.is_displayed(), True)
        self.assertEqual(selection_indicator.text, "100 of 100 selected")
        self.assertIs(select_all_indicator.is_displayed(), False)

        question.click()
        self.assertIs(question.is_displayed(), False)
        self.assertIs(clear.is_displayed(), True)
        self.assertIs(select_all.get_property("checked"), True)
        for hidden_input in select_across:
            self.assertEqual(hidden_input.get_property("value"), "1")
        self.assertIs(selection_indicator.is_displayed(), False)
        self.assertIs(select_all_indicator.is_displayed(), True)

        clear.click()
        self.assertIs(question.is_displayed(), False)
        self.assertIs(clear.is_displayed(), False)
        self.assertIs(select_all.get_property("checked"), False)
        for hidden_input in select_across:
            self.assertEqual(hidden_input.get_property("value"), "0")
        self.assertIs(selection_indicator.is_displayed(), True)
        self.assertEqual(selection_indicator.text, "0 of 100 selected")
        self.assertIs(select_all_indicator.is_displayed(), False)