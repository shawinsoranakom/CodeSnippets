def get_redirect_url(self, request=None):
        """Return the user-originating redirect URL if it's safe.

        Optionally takes a request argument, allowing use outside class-based
        views.
        """
        if request is None:
            request = self.request
        redirect_to = request.POST.get(
            self.redirect_field_name, request.GET.get(self.redirect_field_name)
        )
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(request),
            require_https=request.is_secure(),
        )
        return redirect_to if url_is_safe else ""