def test_access_mixin_permission_denied_response(self):
        user = models.User.objects.create(username="joe", password="qwerty")
        # Authenticated users receive PermissionDenied.
        request = self.factory.get("/rand")
        request.user = user
        view = AlwaysFalseView.as_view()
        with self.assertRaises(PermissionDenied):
            view(request)
        # Anonymous users are redirected to the login page.
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/rand")