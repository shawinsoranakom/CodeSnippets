def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="super",
            password="secret",
            email="super@example.com",
        )
        self.admin_login(
            username="super",
            password="secret",
            login_url=reverse("test_with_sidebar:index"),
        )
        self.selenium.execute_script(
            "localStorage.removeItem('django.admin.navSidebarIsOpen')"
        )