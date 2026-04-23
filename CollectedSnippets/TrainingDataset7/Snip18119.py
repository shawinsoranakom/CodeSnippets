def test_many_permissions_pass(self):
        class AView(PermissionRequiredMixin, EmptyResponseView):
            permission_required = [
                "auth_tests.add_customuser",
                "auth_tests.change_customuser",
            ]

        request = self.factory.get("/rand")
        request.user = self.user
        resp = AView.as_view()(request)
        self.assertEqual(resp.status_code, 200)