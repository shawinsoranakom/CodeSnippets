def execute_basic_operations(self, mode, field_name):
        from selenium.webdriver.common.by import By

        original_url = self.selenium.current_url

        from_box = "#id_%s_from" % field_name
        to_box = "#id_%s_to" % field_name
        choose_button = "id_%s_add" % field_name
        choose_all_button = "id_%s_add_all" % field_name
        remove_button = "id_%s_remove" % field_name
        remove_all_button = "id_%s_remove_all" % field_name

        # Initial positions ---------------------------------------------------
        self.assertSelectOptions(
            from_box,
            [
                str(self.arthur.id),
                str(self.bob.id),
                str(self.cliff.id),
                str(self.jason.id),
                str(self.jenny.id),
                str(self.john.id),
            ],
        )
        self.assertSelectOptions(to_box, [str(self.lisa.id), str(self.peter.id)])
        self.assertButtonsDisabled(
            mode,
            field_name,
            choose_btn_disabled=True,
            remove_btn_disabled=True,
            choose_all_btn_disabled=False,
            remove_all_btn_disabled=False,
        )

        # Click 'Choose all' --------------------------------------------------
        if mode == "horizontal":
            self.selenium.find_element(By.ID, choose_all_button).click()
        elif mode == "vertical":
            # There 's no 'Choose all' button in vertical mode, so individually
            # select all options and click 'Choose'.
            for option in self.selenium.find_elements(
                By.CSS_SELECTOR, from_box + " > option"
            ):
                option.click()
            self.selenium.find_element(By.ID, choose_button).click()
        self.assertSelectOptions(from_box, [])
        self.assertSelectOptions(
            to_box,
            [
                str(self.lisa.id),
                str(self.peter.id),
                str(self.arthur.id),
                str(self.bob.id),
                str(self.cliff.id),
                str(self.jason.id),
                str(self.jenny.id),
                str(self.john.id),
            ],
        )
        self.assertButtonsDisabled(
            mode,
            field_name,
            choose_btn_disabled=True,
            remove_btn_disabled=True,
            choose_all_btn_disabled=True,
            remove_all_btn_disabled=False,
        )

        # Click 'Remove all' --------------------------------------------------
        if mode == "horizontal":
            self.selenium.find_element(By.ID, remove_all_button).click()
        elif mode == "vertical":
            # There 's no 'Remove all' button in vertical mode, so individually
            # select all options and click 'Remove'.
            for option in self.selenium.find_elements(
                By.CSS_SELECTOR, to_box + " > option"
            ):
                option.click()
            self.selenium.find_element(By.ID, remove_button).click()
        self.assertSelectOptions(
            from_box,
            [
                str(self.lisa.id),
                str(self.peter.id),
                str(self.arthur.id),
                str(self.bob.id),
                str(self.cliff.id),
                str(self.jason.id),
                str(self.jenny.id),
                str(self.john.id),
            ],
        )
        self.assertSelectOptions(to_box, [])
        self.assertButtonsDisabled(
            mode,
            field_name,
            choose_btn_disabled=True,
            remove_btn_disabled=True,
            choose_all_btn_disabled=False,
            remove_all_btn_disabled=True,
        )

        # Choose some options ------------------------------------------------
        from_lisa_select_option = self.selenium.find_element(
            By.CSS_SELECTOR, '{} > option[value="{}"]'.format(from_box, self.lisa.id)
        )

        # Check the title attribute is there for tool tips: ticket #20821
        self.assertEqual(
            from_lisa_select_option.get_attribute("title"),
            from_lisa_select_option.get_attribute("text"),
        )

        self.select_option(from_box, str(self.lisa.id))
        self.select_option(from_box, str(self.jason.id))
        self.select_option(from_box, str(self.bob.id))
        self.select_option(from_box, str(self.john.id))
        self.assertButtonsDisabled(
            mode,
            field_name,
            choose_btn_disabled=False,
            remove_btn_disabled=True,
            choose_all_btn_disabled=False,
            remove_all_btn_disabled=True,
        )
        self.selenium.find_element(By.ID, choose_button).click()
        self.assertButtonsDisabled(
            mode,
            field_name,
            choose_btn_disabled=True,
            remove_btn_disabled=True,
            choose_all_btn_disabled=False,
            remove_all_btn_disabled=False,
        )

        self.assertSelectOptions(
            from_box,
            [
                str(self.peter.id),
                str(self.arthur.id),
                str(self.cliff.id),
                str(self.jenny.id),
            ],
        )
        self.assertSelectOptions(
            to_box,
            [
                str(self.lisa.id),
                str(self.bob.id),
                str(self.jason.id),
                str(self.john.id),
            ],
        )

        # Check the tooltip is still there after moving: ticket #20821
        to_lisa_select_option = self.selenium.find_element(
            By.CSS_SELECTOR, '{} > option[value="{}"]'.format(to_box, self.lisa.id)
        )
        self.assertEqual(
            to_lisa_select_option.get_attribute("title"),
            to_lisa_select_option.get_attribute("text"),
        )

        # Remove some options -------------------------------------------------
        self.select_option(to_box, str(self.lisa.id))
        self.select_option(to_box, str(self.bob.id))
        self.assertButtonsDisabled(
            mode,
            field_name,
            choose_btn_disabled=True,
            remove_btn_disabled=False,
            choose_all_btn_disabled=False,
            remove_all_btn_disabled=False,
        )
        self.selenium.find_element(By.ID, remove_button).click()
        self.assertButtonsDisabled(
            mode,
            field_name,
            choose_btn_disabled=True,
            remove_btn_disabled=True,
            choose_all_btn_disabled=False,
            remove_all_btn_disabled=False,
        )

        self.assertSelectOptions(
            from_box,
            [
                str(self.peter.id),
                str(self.arthur.id),
                str(self.cliff.id),
                str(self.jenny.id),
                str(self.lisa.id),
                str(self.bob.id),
            ],
        )
        self.assertSelectOptions(to_box, [str(self.jason.id), str(self.john.id)])

        # Choose some more options --------------------------------------------
        self.select_option(from_box, str(self.arthur.id))
        self.select_option(from_box, str(self.cliff.id))
        self.selenium.find_element(By.ID, choose_button).click()

        self.assertSelectOptions(
            from_box,
            [
                str(self.peter.id),
                str(self.jenny.id),
                str(self.lisa.id),
                str(self.bob.id),
            ],
        )
        self.assertSelectOptions(
            to_box,
            [
                str(self.jason.id),
                str(self.john.id),
                str(self.arthur.id),
                str(self.cliff.id),
            ],
        )

        # Choose some more options --------------------------------------------
        self.select_option(from_box, str(self.peter.id))
        self.select_option(from_box, str(self.lisa.id))

        # Confirm they're selected after clicking inactive buttons: ticket
        # #26575
        self.assertSelectedOptions(from_box, [str(self.peter.id), str(self.lisa.id)])
        self.selenium.find_element(By.ID, remove_button).click()
        self.assertSelectedOptions(from_box, [str(self.peter.id), str(self.lisa.id)])

        # Unselect the options ------------------------------------------------
        self.deselect_option(from_box, str(self.peter.id))
        self.deselect_option(from_box, str(self.lisa.id))

        # Choose some more options --------------------------------------------
        self.select_option(to_box, str(self.jason.id))
        self.select_option(to_box, str(self.john.id))

        # Confirm they're selected after clicking inactive buttons: ticket
        # #26575
        self.assertSelectedOptions(to_box, [str(self.jason.id), str(self.john.id)])
        self.selenium.find_element(By.ID, choose_button).click()
        self.assertSelectedOptions(to_box, [str(self.jason.id), str(self.john.id)])

        # Unselect the options ------------------------------------------------
        self.deselect_option(to_box, str(self.jason.id))
        self.deselect_option(to_box, str(self.john.id))

        # Pressing buttons shouldn't change the URL.
        self.assertEqual(self.selenium.current_url, original_url)