def test_get_redirect_field_name_from_view_func(self):
        def view_func(request):
            return HttpResponse()

        view_func.redirect_field_name = "next_page"
        redirect_field_name = self.middleware.get_redirect_field_name(view_func)
        self.assertEqual(redirect_field_name, "next_page")