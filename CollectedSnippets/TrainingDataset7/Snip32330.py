def test_request(self):
        def get_response(request):
            return HttpResponse(str(request.site.id))

        response = CurrentSiteMiddleware(get_response)(HttpRequest())
        self.assertContains(response, settings.SITE_ID)