def build_absolute_uri(self, location=None):
        """
        Build an absolute URI from the location and the variables available in
        this request. If no ``location`` is specified, build the absolute URI
        using request.get_full_path(). If the location is absolute, convert it
        to an RFC 3987 compliant URI and return it. If location is relative or
        is scheme-relative (i.e., ``//example.com/``), urljoin() it to a base
        URL constructed from the request variables.
        """
        if location is None:
            # Make it an absolute url (but schemeless and domainless) for the
            # edge case that the path starts with '//'.
            location = "//%s" % self.get_full_path()
        else:
            # Coerce lazy locations.
            location = str(location)
        bits = urlsplit(location)
        if not (bits.scheme and bits.netloc):
            # Handle the simple, most common case. If the location is absolute
            # and a scheme or host (netloc) isn't provided, skip an expensive
            # urljoin() as long as no path segments are '.' or '..'.
            if (
                bits.path.startswith("/")
                and not bits.scheme
                and not bits.netloc
                and "/./" not in bits.path
                and "/../" not in bits.path
            ):
                # If location starts with '//' but has no netloc, reuse the
                # schema and netloc from the current request. Strip the double
                # slashes and continue as if it wasn't specified.
                location = self._current_scheme_host + location.removeprefix("//")
            else:
                # Join the constructed URL with the provided location, which
                # allows the provided location to apply query strings to the
                # base path.
                location = urljoin(self._current_scheme_host + self.path, location)
        return iri_to_uri(location)