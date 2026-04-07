def test_many_permissions_in_set_pass(self):
        @permission_required(
            {"auth_tests.add_customuser", "auth_tests.change_customuser"}
        )
        def a_view(request):
            return HttpResponse()

        request = self.factory.get("/rand")
        request.user = self.user
        resp = a_view(request)
        self.assertEqual(resp.status_code, 200)