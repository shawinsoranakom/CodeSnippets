def test_sites_not_installed(self):
        def get_response(request):
            return HttpResponse()

        msg = (
            "You cannot use RedirectFallbackMiddleware when "
            "django.contrib.sites is not installed."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            RedirectFallbackMiddleware(get_response)