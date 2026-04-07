def test_add_inline_link_absent_for_view_only_parent_model(self):
        from selenium.common.exceptions import NoSuchElementException
        from selenium.webdriver.common.by import By

        user = User.objects.create_user("testing", password="password", is_staff=True)
        user.user_permissions.add(
            Permission.objects.get(
                codename="view_poll",
                content_type=ContentType.objects.get_for_model(Poll),
            )
        )
        user.user_permissions.add(
            *Permission.objects.filter(
                codename__endswith="question",
                content_type=ContentType.objects.get_for_model(Question),
            ).values_list("pk", flat=True)
        )
        self.admin_login(username="testing", password="password")
        poll = Poll.objects.create(name="Survey")
        change_url = reverse("admin:admin_inlines_poll_change", args=(poll.id,))
        self.selenium.get(self.live_server_url + change_url)
        with self.disable_implicit_wait():
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(By.LINK_TEXT, "Add another Question")