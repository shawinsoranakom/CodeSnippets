async def test_single_permission_pass_async_view(self):
        @permission_required("auth_tests.add_customuser")
        async def async_view(request):
            return HttpResponse()

        request = self.factory.get("/rand")
        request.auser = self.auser
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)