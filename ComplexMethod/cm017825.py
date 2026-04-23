def _check_referer(self, request):
        referer = request.META.get("HTTP_REFERER")
        if referer is None:
            raise RejectRequest(REASON_NO_REFERER)

        try:
            referer = urlsplit(referer)
        except ValueError:
            raise RejectRequest(REASON_MALFORMED_REFERER)

        # Make sure we have a valid URL for Referer.
        if "" in (referer.scheme, referer.netloc):
            raise RejectRequest(REASON_MALFORMED_REFERER)

        # Ensure that our Referer is also secure.
        if referer.scheme != "https":
            raise RejectRequest(REASON_INSECURE_REFERER)

        if any(
            is_same_domain(referer.netloc, host)
            for host in self.csrf_trusted_origins_hosts
        ):
            return
        # Allow matching the configured cookie domain.
        good_referer = (
            settings.SESSION_COOKIE_DOMAIN
            if settings.CSRF_USE_SESSIONS
            else settings.CSRF_COOKIE_DOMAIN
        )
        if good_referer is None:
            # If no cookie domain is configured, allow matching the current
            # host:port exactly if it's permitted by ALLOWED_HOSTS.
            try:
                # request.get_host() includes the port.
                good_referer = request.get_host()
            except DisallowedHost:
                raise RejectRequest(REASON_BAD_REFERER % referer.geturl())
        else:
            server_port = request.get_port()
            if server_port not in ("443", "80"):
                good_referer = "%s:%s" % (good_referer, server_port)

        if not is_same_domain(referer.netloc, good_referer):
            raise RejectRequest(REASON_BAD_REFERER % referer.geturl())