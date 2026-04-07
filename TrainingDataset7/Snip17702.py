async def test_decorator_async_view_async_test_func(self):
        async def async_test_func(user):
            return await user.ahas_perms(["auth_tests.add_customuser"])

        @user_passes_test(async_test_func)
        async def async_view(request):
            return HttpResponse()

        request = self.factory.get("/rand")
        request.auser = self.auser_pass
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)

        request.auser = self.auser_deny
        response = await async_view(request)
        self.assertEqual(response.status_code, 302)