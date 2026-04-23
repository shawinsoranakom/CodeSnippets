def _origin_verified(self, request):
        request_origin = request.META["HTTP_ORIGIN"]
        try:
            good_host = request.get_host()
        except DisallowedHost:
            pass
        else:
            good_origin = "%s://%s" % (
                "https" if request.is_secure() else "http",
                good_host,
            )
            if request_origin == good_origin:
                return True
        if request_origin in self.allowed_origins_exact:
            return True
        try:
            parsed_origin = urlsplit(request_origin)
        except ValueError:
            return False
        parsed_origin_scheme = parsed_origin.scheme
        parsed_origin_netloc = parsed_origin.netloc
        return any(
            is_same_domain(parsed_origin_netloc, host)
            for host in self.allowed_origin_subdomains.get(parsed_origin_scheme, ())
        )