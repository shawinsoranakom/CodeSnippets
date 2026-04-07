def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(request, "csrf_processing_done", False):
            return None

        # Wait until request.META["CSRF_COOKIE"] has been manipulated before
        # bailing out, so that get_token still works
        if getattr(callback, "csrf_exempt", False):
            return None

        # Assume that anything not defined as 'safe' by RFC 9110 needs
        # protection
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self._accept(request)

        if getattr(request, "_dont_enforce_csrf_checks", False):
            # Mechanism to turn off CSRF checks for test suite. It comes after
            # the creation of CSRF cookies, so that everything else continues
            # to work exactly the same (e.g. cookies are sent, etc.), but
            # before any branches that call the _reject method.
            return self._accept(request)

        # Reject the request if the Origin header doesn't match an allowed
        # value.
        if "HTTP_ORIGIN" in request.META:
            if not self._origin_verified(request):
                return self._reject(
                    request, REASON_BAD_ORIGIN % request.META["HTTP_ORIGIN"]
                )
        elif request.is_secure():
            # If the Origin header wasn't provided, reject HTTPS requests if
            # the Referer header doesn't match an allowed value.
            #
            # Suppose user visits http://example.com/
            # An active network attacker (man-in-the-middle, MITM) sends a
            # POST form that targets https://example.com/detonate-bomb/ and
            # submits it via JavaScript.
            #
            # The attacker will need to provide a CSRF cookie and token, but
            # that's no problem for a MITM and the session-independent secret
            # we're using. So the MITM can circumvent the CSRF protection. This
            # is true for any HTTP connection, but anyone using HTTPS expects
            # better! For this reason, for https://example.com/ we need
            # additional protection that treats http://example.com/ as
            # completely untrusted. Under HTTPS, Barth et al. found that the
            # Referer header is missing for same-domain requests in only about
            # 0.2% of cases or less, so we can use strict Referer checking.
            try:
                self._check_referer(request)
            except RejectRequest as exc:
                return self._reject(request, exc.reason)

        try:
            self._check_token(request)
        except RejectRequest as exc:
            return self._reject(request, exc.reason)

        return self._accept(request)