def is_ignorable_request(self, request, uri, domain, referer):
        """
        Return True if the given request *shouldn't* notify the site managers
        according to project settings or in situations outlined by the inline
        comments.
        """
        # The referer is empty.
        if not referer:
            return True

        # APPEND_SLASH is enabled and the referer is equal to the current URL
        # without a trailing slash indicating an internal redirect.
        if settings.APPEND_SLASH and uri.endswith("/") and referer == uri[:-1]:
            return True

        # A '?' in referer is identified as a search engine source.
        if not self.is_internal_request(domain, referer) and "?" in referer:
            return True

        # The referer is equal to the current URL, ignoring the scheme (assumed
        # to be a poorly implemented bot).
        parsed_referer = urlsplit(referer)
        if parsed_referer.netloc in ["", domain] and parsed_referer.path == uri:
            return True

        return any(pattern.search(uri) for pattern in settings.IGNORABLE_404_URLS)