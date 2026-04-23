def test_related_object_add_js_actions(self):
        from selenium.webdriver.common.by import By

        add_url = reverse("admin:admin_views_camelcaserelatedmodel_add")
        self.selenium.get(self.live_server_url + add_url)
        m2m_to = self.selenium.find_element(By.ID, "id_m2m_to")
        m2m_box = self.selenium.find_element(By.ID, "id_m2m_from")
        fk_dropdown = self.selenium.find_element(By.ID, "id_fk")

        # Add new related entry using +.
        name = "Bergeron"
        self.selenium.find_element(By.ID, "add_id_m2m").click()
        self.wait_for_and_switch_to_popup()
        self.selenium.find_element(By.ID, "id_interesting_name").send_keys(name)
        self.selenium.find_element(By.NAME, "_save").click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])

        id_value = CamelCaseModel.objects.get(interesting_name=name).id

        # Check the new value correctly appears in the "to" box.
        self.assertHTMLEqual(
            m2m_to.get_attribute("innerHTML"),
            f"""<option title="{name}" value="{id_value}">{name}</option>""",
        )
        self.assertHTMLEqual(m2m_box.get_attribute("innerHTML"), "")
        self.assertHTMLEqual(
            fk_dropdown.get_attribute("innerHTML"),
            f"""
            <option value="" selected>---------</option>
            <option value="{id_value}">{name}</option>
            """,
        )

        # Move the new value to the from box.
        self.selenium.find_element(By.XPATH, "//*[@id='id_m2m_to']/option").click()
        self.selenium.find_element(By.XPATH, "//*[@id='id_m2m_remove']").click()

        self.assertHTMLEqual(
            m2m_box.get_attribute("innerHTML"),
            f"""<option title="{name}" value="{id_value}">{name}</option>""",
        )
        self.assertHTMLEqual(m2m_to.get_attribute("innerHTML"), "")

        # Move the new value to the to box.
        self.selenium.find_element(By.XPATH, "//*[@id='id_m2m_from']/option").click()
        self.selenium.find_element(By.XPATH, "//*[@id='id_m2m_add']").click()

        self.assertHTMLEqual(m2m_box.get_attribute("innerHTML"), "")
        self.assertHTMLEqual(
            m2m_to.get_attribute("innerHTML"),
            f"""<option title="{name}" value="{id_value}">{name}</option>""",
        )