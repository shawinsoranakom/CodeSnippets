def test_filter(self):
        """
        Typing in the search box filters out options displayed in the 'from'
        box.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        self.school.students.set([self.lisa, self.peter])
        self.school.alumni.set([self.lisa, self.peter])

        with self.small_screen_size():
            self.admin_login(username="super", password="secret", login_url="/")
            self.selenium.get(
                self.live_server_url
                + reverse("admin:admin_widgets_school_change", args=(self.school.id,))
            )

            for field_name in ["students", "alumni"]:
                from_box = "#id_%s_from" % field_name
                to_box = "#id_%s_to" % field_name
                choose_link = "id_%s_add" % field_name
                remove_link = "id_%s_remove" % field_name
                input = self.selenium.find_element(By.ID, "id_%s_input" % field_name)
                # Initial values.
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
                # Typing in some characters filters out non-matching options.
                input.send_keys("a")
                self.assertSelectOptions(
                    from_box, [str(self.arthur.id), str(self.jason.id)]
                )
                input.send_keys("R")
                self.assertSelectOptions(from_box, [str(self.arthur.id)])
                # Clearing the text box makes the other options reappear.
                input.send_keys([Keys.BACK_SPACE])
                self.assertSelectOptions(
                    from_box, [str(self.arthur.id), str(self.jason.id)]
                )
                input.send_keys([Keys.BACK_SPACE])
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

                # Choosing a filtered option sends it properly to the 'to' box.
                input.send_keys("a")
                self.assertSelectOptions(
                    from_box, [str(self.arthur.id), str(self.jason.id)]
                )
                self.select_option(from_box, str(self.jason.id))
                self.selenium.find_element(By.ID, choose_link).click()
                self.assertSelectOptions(from_box, [str(self.arthur.id)])
                self.assertSelectOptions(
                    to_box,
                    [
                        str(self.lisa.id),
                        str(self.peter.id),
                        str(self.jason.id),
                    ],
                )

                self.select_option(to_box, str(self.lisa.id))
                self.selenium.find_element(By.ID, remove_link).click()
                self.assertSelectOptions(
                    from_box, [str(self.arthur.id), str(self.lisa.id)]
                )
                self.assertSelectOptions(
                    to_box, [str(self.peter.id), str(self.jason.id)]
                )

                input.send_keys([Keys.BACK_SPACE])  # Clear text box
                self.assertSelectOptions(
                    from_box,
                    [
                        str(self.arthur.id),
                        str(self.bob.id),
                        str(self.cliff.id),
                        str(self.jenny.id),
                        str(self.john.id),
                        str(self.lisa.id),
                    ],
                )
                self.assertSelectOptions(
                    to_box, [str(self.peter.id), str(self.jason.id)]
                )

                # Pressing enter on a filtered option sends it properly to
                # the 'to' box.
                self.select_option(to_box, str(self.jason.id))
                self.selenium.find_element(By.ID, remove_link).click()
                input.send_keys("ja")
                self.assertSelectOptions(from_box, [str(self.jason.id)])
                input.send_keys([Keys.ENTER])
                self.assertSelectOptions(
                    to_box, [str(self.peter.id), str(self.jason.id)]
                )
                input.send_keys([Keys.BACK_SPACE, Keys.BACK_SPACE])

            # Save, everything should be stored properly in the database.
            with self.wait_page_loaded():
                self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.school = School.objects.get(id=self.school.id)  # Reload from database
        self.assertEqual(list(self.school.students.all()), [self.jason, self.peter])
        self.assertEqual(list(self.school.alumni.all()), [self.jason, self.peter])