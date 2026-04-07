def test_get_login_url_from_view_func(self):
        def view_func(request):
            return HttpResponse()

        view_func.login_url = "/custom_login/"
        login_url = self.middleware.get_login_url(view_func)
        self.assertEqual(login_url, "/custom_login/")