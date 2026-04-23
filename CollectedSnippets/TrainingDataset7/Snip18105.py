def test_access_mixin_permission_denied_remote_login_url(self):
        class AView(AlwaysFalseView):
            login_url = "https://www.remote.example.com/login"

        view = AView.as_view()
        request = self.factory.get("/rand")
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "https://www.remote.example.com/login?next=http%3A//testserver/rand",
        )