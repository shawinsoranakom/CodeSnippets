def normalize(url):
            """Sort the URL's query string parameters."""
            url = str(url)  # Coerce reverse_lazy() URLs.
            scheme, netloc, path, query, fragment = urlsplit(url)
            query_parts = sorted(parse_qsl(query))
            return urlunsplit((scheme, netloc, path, urlencode(query_parts), fragment))