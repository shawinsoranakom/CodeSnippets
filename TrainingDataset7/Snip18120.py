def test_single_permission_pass(self):
        class AView(PermissionRequiredMixin, EmptyResponseView):
            permission_required = "auth_tests.add_customuser"

        request = self.factory.get("/rand")
        request.user = self.user
        resp = AView.as_view()(request)
        self.assertEqual(resp.status_code, 200)