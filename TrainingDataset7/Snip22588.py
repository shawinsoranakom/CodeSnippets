def test_float_field_rendering_passes_client_side_validation(self):
        """
        Rendered widget allows non-integer value with the client-side
        validation.
        """
        from selenium.webdriver.common.by import By

        self.selenium.get(self.live_server_url + reverse("form_view"))
        number_input = self.selenium.find_element(By.ID, "id_number")
        number_input.send_keys("0.5")
        is_valid = self.selenium.execute_script(
            "return document.getElementById('id_number').checkValidity()"
        )
        self.assertTrue(is_valid)