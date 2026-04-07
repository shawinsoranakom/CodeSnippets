async def test_many_permissions_pass_async_view(self):
        @permission_required(
            ["auth_tests.add_customuser", "auth_tests.change_customuser"]
        )
        async def async_view(request):
            return HttpResponse()

        request = self.factory.get("/rand")
        request.auser = self.auser
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)