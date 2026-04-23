def test_related_object_update_with_camel_casing(self):
        from selenium.webdriver.common.by import By

        add_url = reverse("admin:admin_views_camelcaserelatedmodel_add")
        self.selenium.get(self.live_server_url + add_url)
        interesting_name = "A test name"

        # Add a new CamelCaseModel using the "+" icon next to the "fk" field.
        self.selenium.find_element(By.ID, "add_id_fk").click()

        # Switch to the add popup window.
        self.wait_for_and_switch_to_popup()

        # Find the "interesting_name" field and enter a value, then save it.
        self.selenium.find_element(By.ID, "id_interesting_name").send_keys(
            interesting_name
        )
        self.selenium.find_element(By.NAME, "_save").click()

        # Return to the main window.
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])

        id_value = CamelCaseModel.objects.get(interesting_name=interesting_name).id

        # Check that both the "Available" m2m box and the "Fk" dropdown now
        # include the newly added CamelCaseModel instance.
        fk_dropdown = self.selenium.find_element(By.ID, "id_fk")
        self.assertHTMLEqual(
            fk_dropdown.get_attribute("innerHTML"),
            f"""
            <option value="" selected="">---------</option>
            <option value="{id_value}" selected>{interesting_name}</option>
            """,
        )
        # Check the newly added instance is not also added in the "to" box.
        m2m_to = self.selenium.find_element(By.ID, "id_m2m_to")
        self.assertHTMLEqual(m2m_to.get_attribute("innerHTML"), "")
        m2m_box = self.selenium.find_element(By.ID, "id_m2m_from")
        self.assertHTMLEqual(
            m2m_box.get_attribute("innerHTML"),
            f"""
            <option title="{interesting_name}" value="{id_value}">
            {interesting_name}</option>
            """,
        )