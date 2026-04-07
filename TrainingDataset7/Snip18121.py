def test_permissioned_denied_redirect(self):
        class AView(PermissionRequiredMixin, EmptyResponseView):
            permission_required = [
                "auth_tests.add_customuser",
                "auth_tests.change_customuser",
                "nonexistent-permission",
            ]

        # Authenticated users receive PermissionDenied.
        request = self.factory.get("/rand")
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            AView.as_view()(request)
        # Anonymous users are redirected to the login page.
        request.user = AnonymousUser()
        resp = AView.as_view()(request)
        self.assertEqual(resp.status_code, 302)