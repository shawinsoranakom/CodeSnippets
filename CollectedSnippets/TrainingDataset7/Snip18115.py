def test_user_passes(self):
        view = AlwaysTrueView.as_view()
        request = self.factory.get("/rand")
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 200)