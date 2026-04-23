def test_updating_related_objects_updates_fk_selects_except_autocompletes(self):
        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        born_country_select_id = "id_born_country"
        living_country_select_id = "id_living_country"
        living_country_select2_textbox_id = "select2-id_living_country-container"
        favorite_country_to_vacation_select_id = "id_favorite_country_to_vacation"
        continent_select_id = "id_continent"

        def _get_HTML_inside_element_by_id(id_):
            return self.selenium.find_element(By.ID, id_).get_attribute("innerHTML")

        def _get_text_inside_element_by_selector(selector):
            return self.selenium.find_element(By.CSS_SELECTOR, selector).get_attribute(
                "innerText"
            )

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        add_url = reverse("admin:admin_views_traveler_add")
        self.selenium.get(self.live_server_url + add_url)

        # Add new Country from the born_country select.
        self.selenium.find_element(By.ID, f"add_{born_country_select_id}").click()
        self.wait_for_and_switch_to_popup()
        self.selenium.find_element(By.ID, "id_name").send_keys("Argentina")
        continent_select = Select(
            self.selenium.find_element(By.ID, continent_select_id)
        )
        continent_select.select_by_visible_text("South America")
        self.selenium.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])

        argentina = Country.objects.get(name="Argentina")
        self.assertHTMLEqual(
            _get_HTML_inside_element_by_id(born_country_select_id),
            f"""
            <option value="" selected="">---------</option>
            <option value="{argentina.pk}" selected="">Argentina</option>
            """,
        )
        # Argentina isn't added to the living_country select nor selected by
        # the select2 widget.
        self.assertEqual(
            _get_text_inside_element_by_selector(f"#{living_country_select_id}"), ""
        )
        self.assertEqual(
            _get_text_inside_element_by_selector(
                f"#{living_country_select2_textbox_id}"
            ),
            "",
        )
        # Argentina won't appear because favorite_country_to_vacation field has
        # limit_choices_to.
        self.assertHTMLEqual(
            _get_HTML_inside_element_by_id(favorite_country_to_vacation_select_id),
            '<option value="" selected="">---------</option>',
        )

        # Add new Country from the living_country select.
        element = self.selenium.find_element(By.ID, f"add_{living_country_select_id}")
        ActionChains(self.selenium).move_to_element(element).click(element).perform()
        self.wait_for_and_switch_to_popup()
        self.selenium.find_element(By.ID, "id_name").send_keys("Spain")
        continent_select = Select(
            self.selenium.find_element(By.ID, continent_select_id)
        )
        continent_select.select_by_visible_text("Europe")
        self.selenium.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])

        spain = Country.objects.get(name="Spain")
        self.assertHTMLEqual(
            _get_HTML_inside_element_by_id(born_country_select_id),
            f"""
            <option value="" selected="">---------</option>
            <option value="{argentina.pk}" selected="">Argentina</option>
            <option value="{spain.pk}">Spain</option>
            """,
        )

        # Spain is added to the living_country select and it's also selected by
        # the select2 widget.
        self.assertEqual(
            _get_text_inside_element_by_selector(f"#{living_country_select_id} option"),
            "Spain",
        )
        self.assertEqual(
            _get_text_inside_element_by_selector(
                f"#{living_country_select2_textbox_id}"
            ),
            "Spain",
        )
        # Spain won't appear because favorite_country_to_vacation field has
        # limit_choices_to.
        self.assertHTMLEqual(
            _get_HTML_inside_element_by_id(favorite_country_to_vacation_select_id),
            '<option value="" selected="">---------</option>',
        )

        # Edit second Country created from living_country select.
        favorite_select = Select(
            self.selenium.find_element(By.ID, living_country_select_id)
        )
        favorite_select.select_by_visible_text("Spain")
        self.selenium.find_element(By.ID, f"change_{living_country_select_id}").click()
        self.wait_for_and_switch_to_popup()
        favorite_name_input = self.selenium.find_element(By.ID, "id_name")
        favorite_name_input.clear()
        favorite_name_input.send_keys("Italy")
        self.selenium.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])

        italy = spain
        self.assertHTMLEqual(
            _get_HTML_inside_element_by_id(born_country_select_id),
            f"""
            <option value="" selected="">---------</option>
            <option value="{argentina.pk}" selected="">Argentina</option>
            <option value="{italy.pk}">Italy</option>
            """,
        )
        # Italy is added to the living_country select and it's also selected by
        # the select2 widget.
        self.assertEqual(
            _get_text_inside_element_by_selector(f"#{living_country_select_id} option"),
            "Italy",
        )
        self.assertEqual(
            _get_text_inside_element_by_selector(
                f"#{living_country_select2_textbox_id}"
            ),
            "Italy",
        )
        # favorite_country_to_vacation field has no options.
        self.assertHTMLEqual(
            _get_HTML_inside_element_by_id(favorite_country_to_vacation_select_id),
            '<option value="" selected="">---------</option>',
        )

        # Add a new Asian country.
        self.selenium.find_element(
            By.ID, f"add_{favorite_country_to_vacation_select_id}"
        ).click()
        self.wait_for_and_switch_to_popup()
        favorite_name_input = self.selenium.find_element(By.ID, "id_name")
        favorite_name_input.send_keys("Qatar")
        continent_select = Select(
            self.selenium.find_element(By.ID, continent_select_id)
        )
        continent_select.select_by_visible_text("Asia")
        self.selenium.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])

        # Submit the new Traveler.
        with self.wait_page_loaded():
            self.selenium.find_element(By.CSS_SELECTOR, '[name="_save"]').click()
        traveler = Traveler.objects.get()
        self.assertEqual(traveler.born_country.name, "Argentina")
        self.assertEqual(traveler.living_country.name, "Italy")
        self.assertEqual(traveler.favorite_country_to_vacation.name, "Qatar")