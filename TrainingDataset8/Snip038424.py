def parse_url_path(self, url_path: str) -> str:
        url_parts = url_path.split("/")

        maybe_page_name = url_parts[0]
        if maybe_page_name in self._pages:
            # If we're trying to navigate to a page, we return "index.html"
            # directly here instead of deferring to the superclass below after
            # modifying the url_path. The reason why is that tornado handles
            # requests to "directories" (which is what navigating to a page
            # looks like) by appending a trailing '/' if there is none and
            # redirecting.
            #
            # This would work, but it
            #   * adds an unnecessary redirect+roundtrip
            #   * adds a trailing '/' to the URL appearing in the browser, which
            #     looks bad
            if len(url_parts) == 1:
                return "index.html"

            url_path = "/".join(url_parts[1:])

        return super().parse_url_path(url_path)