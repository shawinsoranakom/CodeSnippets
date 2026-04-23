def test_login_required(self):
        """
        login_required works on a simple view wrapped in a login_required
        decorator.
        """

        class AView(LoginRequiredMixin, EmptyResponseView):
            pass

        view = AView.as_view()

        request = self.factory.get("/rand")
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/accounts/login/?next=/rand", response.url)
        request = self.factory.get("/rand")
        request.user = self.user
        response = view(request)
        self.assertEqual(response.status_code, 200)