def test_single_permission_pass(self):
        @permission_required("auth_tests.add_customuser")
        def a_view(request):
            return HttpResponse()

        request = self.factory.get("/rand")
        request.user = self.user
        resp = a_view(request)
        self.assertEqual(resp.status_code, 200)