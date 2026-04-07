def test_input_element_font(self):
        """
        Browsers' default stylesheets override the font of inputs. The admin
        adds additional CSS to handle this.
        """
        from selenium.webdriver.common.by import By

        self.selenium.get(self.live_server_url + reverse("admin:login"))
        element = self.selenium.find_element(By.ID, "id_username")
        # Some browsers quotes the fonts, some don't.
        fonts = [
            font.strip().strip('"')
            for font in element.value_of_css_property("font-family").split(",")
        ]
        self.assertEqual(
            fonts,
            [
                "Segoe UI",
                "system-ui",
                "Roboto",
                "Helvetica Neue",
                "Arial",
                "sans-serif",
                "Apple Color Emoji",
                "Segoe UI Emoji",
                "Segoe UI Symbol",
                "Noto Color Emoji",
            ],
        )