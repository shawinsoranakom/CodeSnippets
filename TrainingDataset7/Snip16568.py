def test_prepopulated_fields(self):
        """
        The JavaScript-automated prepopulated fields work with the main form
        and with stacked and tabular inlines.
        Refs #13068, #9264, #9983, #9784.
        """
        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_mainprepopulated_add")
        )
        self.wait_for(".select2")

        # Main form ----------------------------------------------------------
        self.selenium.find_element(By.ID, "id_pubdate").send_keys("2012-02-18")
        status = self.selenium.find_element(By.ID, "id_status")
        ActionChains(self.selenium).move_to_element(status).click(status).perform()
        self.select_option("#id_status", "option two")
        self.selenium.find_element(By.ID, "id_name").send_keys(
            " the mAin nÀMë and it's awεšomeıııİ"
        )
        slug1 = self.selenium.find_element(By.ID, "id_slug1").get_attribute("value")
        slug2 = self.selenium.find_element(By.ID, "id_slug2").get_attribute("value")
        slug3 = self.selenium.find_element(By.ID, "id_slug3").get_attribute("value")
        self.assertEqual(slug1, "the-main-name-and-its-awesomeiiii-2012-02-18")
        self.assertEqual(slug2, "option-two-the-main-name-and-its-awesomeiiii")
        self.assertEqual(
            slug3, "the-main-n\xe0m\xeb-and-its-aw\u03b5\u0161ome\u0131\u0131\u0131i"
        )

        # Stacked inlines with fieldsets -------------------------------------
        # Initial inline
        self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-0-pubdate"
        ).send_keys("2011-12-17")
        status = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-0-status"
        )
        ActionChains(self.selenium).move_to_element(status).click(status).perform()
        self.select_option("#id_relatedprepopulated_set-0-status", "option one")
        self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-0-name"
        ).send_keys(" here is a sŤāÇkeð   inline !  ")
        slug1 = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-0-slug1"
        ).get_attribute("value")
        slug2 = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-0-slug2"
        ).get_attribute("value")
        self.assertEqual(slug1, "here-is-a-stacked-inline-2011-12-17")
        self.assertEqual(slug2, "option-one-here-is-a-stacked-inline")
        initial_select2_inputs = self.selenium.find_elements(
            By.CLASS_NAME, "select2-selection"
        )
        # Inline formsets have empty/invisible forms.
        # Only the 4 visible select2 inputs are initialized.
        num_initial_select2_inputs = len(initial_select2_inputs)
        self.assertEqual(num_initial_select2_inputs, 4)

        # Add an inline
        self.selenium.find_elements(By.LINK_TEXT, "Add another Related prepopulated")[
            0
        ].click()
        self.assertEqual(
            len(self.selenium.find_elements(By.CLASS_NAME, "select2-selection")),
            num_initial_select2_inputs + 2,
        )
        self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-1-pubdate"
        ).send_keys("1999-01-25")
        status = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-1-status"
        )
        ActionChains(self.selenium).move_to_element(status).click(status).perform()
        self.select_option("#id_relatedprepopulated_set-1-status", "option two")
        self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-1-name"
        ).send_keys(
            " now you haVe anöther   sŤāÇkeð  inline with a very ... "
            "loooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooog "
            "text... "
        )
        slug1 = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-1-slug1"
        ).get_attribute("value")
        slug2 = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-1-slug2"
        ).get_attribute("value")
        # 50 characters maximum for slug1 field
        self.assertEqual(slug1, "now-you-have-another-stacked-inline-with-a-very-lo")
        # 60 characters maximum for slug2 field
        self.assertEqual(
            slug2, "option-two-now-you-have-another-stacked-inline-with-a-very-l"
        )

        # Tabular inlines ----------------------------------------------------
        # Initial inline
        status = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-0-status"
        )
        # Fix for Firefox which does not scroll to clicked elements
        # automatically with the Options API
        self.selenium.execute_script("arguments[0].scrollIntoView();", status)
        ActionChains(self.selenium).move_to_element(status).click(status).perform()
        self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-0-pubdate"
        ).send_keys("1234-12-07")
        self.select_option("#id_relatedprepopulated_set-2-0-status", "option two")
        self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-0-name"
        ).send_keys("And now, with a tÃbűlaŘ inline !!!")
        slug1 = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-0-slug1"
        ).get_attribute("value")
        slug2 = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-0-slug2"
        ).get_attribute("value")
        self.assertEqual(slug1, "and-now-with-a-tabular-inline-1234-12-07")
        self.assertEqual(slug2, "option-two-and-now-with-a-tabular-inline")

        # Add an inline
        # Button may be outside the browser frame.
        element = self.selenium.find_elements(
            By.LINK_TEXT, "Add another Related prepopulated"
        )[1]
        self.selenium.execute_script("window.scrollTo(0, %s);" % element.location["y"])
        element.click()
        self.assertEqual(
            len(self.selenium.find_elements(By.CLASS_NAME, "select2-selection")),
            num_initial_select2_inputs + 4,
        )
        self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-1-pubdate"
        ).send_keys("1981-08-22")
        status = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-1-status"
        )
        self.selenium.execute_script("arguments[0].scrollIntoView();", status)
        ActionChains(self.selenium).move_to_element(status).click(status).perform()
        self.select_option("#id_relatedprepopulated_set-2-1-status", "option one")
        self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-1-name"
        ).send_keys(r'tÃbűlaŘ inline with ignored ;"&*^\%$#@-/`~ characters')
        slug1 = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-1-slug1"
        ).get_attribute("value")
        slug2 = self.selenium.find_element(
            By.ID, "id_relatedprepopulated_set-2-1-slug2"
        ).get_attribute("value")
        self.assertEqual(slug1, "tabular-inline-with-ignored-characters-1981-08-22")
        self.assertEqual(slug2, "option-one-tabular-inline-with-ignored-characters")
        # Add an inline without an initial inline.
        # The button is outside of the browser frame.
        self.selenium.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.selenium.find_elements(By.LINK_TEXT, "Add another Related prepopulated")[
            2
        ].click()
        self.assertEqual(
            len(self.selenium.find_elements(By.CLASS_NAME, "select2-selection")),
            num_initial_select2_inputs + 6,
        )
        # Stacked Inlines without fieldsets ----------------------------------
        # Initial inline.
        row_id = "id_relatedprepopulated_set-4-0-"
        self.selenium.find_element(By.ID, f"{row_id}pubdate").send_keys("2011-12-12")
        status = self.selenium.find_element(By.ID, f"{row_id}status")
        self.selenium.execute_script("arguments[0].scrollIntoView();", status)
        ActionChains(self.selenium).move_to_element(status).click(status).perform()
        self.select_option(f"#{row_id}status", "option one")
        self.selenium.find_element(By.ID, f"{row_id}name").send_keys(
            " sŤāÇkeð  inline !  "
        )
        slug1 = self.selenium.find_element(By.ID, f"{row_id}slug1").get_attribute(
            "value"
        )
        slug2 = self.selenium.find_element(By.ID, f"{row_id}slug2").get_attribute(
            "value"
        )
        self.assertEqual(slug1, "stacked-inline-2011-12-12")
        self.assertEqual(slug2, "option-one")
        # Add inline.
        add_link = self.selenium.find_elements(
            By.LINK_TEXT,
            "Add another Related prepopulated",
        )[3]
        self.selenium.execute_script("arguments[0].scrollIntoView();", add_link)
        add_link.click()
        row_id = "id_relatedprepopulated_set-4-1-"
        self.selenium.find_element(By.ID, f"{row_id}pubdate").send_keys("1999-01-20")
        status = self.selenium.find_element(By.ID, f"{row_id}status")
        self.selenium.execute_script("arguments[0].scrollIntoView();", status)
        ActionChains(self.selenium).move_to_element(status).click(status).perform()
        self.select_option(f"#{row_id}status", "option two")
        self.selenium.find_element(By.ID, f"{row_id}name").send_keys(
            " now you haVe anöther   sŤāÇkeð  inline with a very loooong "
        )
        slug1 = self.selenium.find_element(By.ID, f"{row_id}slug1").get_attribute(
            "value"
        )
        slug2 = self.selenium.find_element(By.ID, f"{row_id}slug2").get_attribute(
            "value"
        )
        self.assertEqual(slug1, "now-you-have-another-stacked-inline-with-a-very-lo")
        self.assertEqual(slug2, "option-two")

        # Save and check that everything is properly stored in the database
        with self.wait_page_loaded():
            self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.assertEqual(MainPrepopulated.objects.count(), 1)
        MainPrepopulated.objects.get(
            name=" the mAin nÀMë and it's awεšomeıııİ",
            pubdate="2012-02-18",
            status="option two",
            slug1="the-main-name-and-its-awesomeiiii-2012-02-18",
            slug2="option-two-the-main-name-and-its-awesomeiiii",
            slug3="the-main-nàmë-and-its-awεšomeıııi",
        )
        self.assertEqual(RelatedPrepopulated.objects.count(), 6)
        RelatedPrepopulated.objects.get(
            name=" here is a sŤāÇkeð   inline !  ",
            pubdate="2011-12-17",
            status="option one",
            slug1="here-is-a-stacked-inline-2011-12-17",
            slug2="option-one-here-is-a-stacked-inline",
        )
        RelatedPrepopulated.objects.get(
            # 75 characters in name field
            name=(
                " now you haVe anöther   sŤāÇkeð  inline with a very ... "
                "loooooooooooooooooo"
            ),
            pubdate="1999-01-25",
            status="option two",
            slug1="now-you-have-another-stacked-inline-with-a-very-lo",
            slug2="option-two-now-you-have-another-stacked-inline-with-a-very-l",
        )
        RelatedPrepopulated.objects.get(
            name="And now, with a tÃbűlaŘ inline !!!",
            pubdate="1234-12-07",
            status="option two",
            slug1="and-now-with-a-tabular-inline-1234-12-07",
            slug2="option-two-and-now-with-a-tabular-inline",
        )
        RelatedPrepopulated.objects.get(
            name=r'tÃbűlaŘ inline with ignored ;"&*^\%$#@-/`~ characters',
            pubdate="1981-08-22",
            status="option one",
            slug1="tabular-inline-with-ignored-characters-1981-08-22",
            slug2="option-one-tabular-inline-with-ignored-characters",
        )