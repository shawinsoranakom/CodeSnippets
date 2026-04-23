def _test_redirect(self, view=None, url="/accounts/login/?next=/rand"):
        if not view:
            view = AlwaysFalseView.as_view()
        request = self.factory.get("/rand")
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)