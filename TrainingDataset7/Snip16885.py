def test_refresh_page(self):
        """
        Horizontal and vertical filter widgets keep selected options on page
        reload (#22955).
        """
        self.school.students.add(self.arthur, self.jason)
        self.school.alumni.add(self.arthur, self.jason)

        self.admin_login(username="super", password="secret", login_url="/")
        change_url = reverse(
            "admin:admin_widgets_school_change", args=(self.school.id,)
        )
        self.selenium.get(self.live_server_url + change_url)

        self.assertCountSeleniumElements("#id_students_to > option", 2)

        # self.selenium.refresh() or send_keys(Keys.F5) does hard reload and
        # doesn't replicate what happens when a user clicks the browser's
        # 'Refresh' button.
        with self.wait_page_loaded():
            self.selenium.execute_script("location.reload()")

        self.assertCountSeleniumElements("#id_students_to > option", 2)