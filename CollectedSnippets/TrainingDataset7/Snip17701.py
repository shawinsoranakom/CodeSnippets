async def test_decorator_async_view(self):
        def sync_test_func(user):
            return bool(
                models.Group.objects.filter(name__istartswith=user.username).exists()
            )

        @user_passes_test(sync_test_func)
        async def async_view(request):
            return HttpResponse()

        request = self.factory.get("/rand")
        request.auser = self.auser_pass
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)

        request.auser = self.auser_deny
        response = await async_view(request)
        self.assertEqual(response.status_code, 302)