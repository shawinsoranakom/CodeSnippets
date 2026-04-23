async def test_login_required_async_view(self, login_url=None):
        async def async_view(request):
            return HttpResponse()

        async def auser_anonymous():
            return models.AnonymousUser()

        async def auser():
            return self.u1

        if login_url is None:
            async_view = login_required(async_view)
            login_url = settings.LOGIN_URL
        else:
            async_view = login_required(async_view, login_url=login_url)

        request = self.factory.get("/rand")
        request.auser = auser_anonymous
        response = await async_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(login_url, response.url)

        request.auser = auser
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)