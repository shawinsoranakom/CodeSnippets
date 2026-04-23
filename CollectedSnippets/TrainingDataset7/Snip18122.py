def test_permissioned_denied_exception_raised(self):
        class AView(PermissionRequiredMixin, EmptyResponseView):
            permission_required = [
                "auth_tests.add_customuser",
                "auth_tests.change_customuser",
                "nonexistent-permission",
            ]
            raise_exception = True

        request = self.factory.get("/rand")
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            AView.as_view()(request)