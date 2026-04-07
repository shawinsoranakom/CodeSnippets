def _get_full_path(self, path, force_append_slash):
        # RFC 3986 requires query string arguments to be in the ASCII range.
        # Rather than crash if this doesn't happen, we encode defensively.
        return "%s%s%s" % (
            escape_uri_path(path),
            "/" if force_append_slash and not path.endswith("/") else "",
            (
                ("?" + iri_to_uri(self.META.get("QUERY_STRING", "")))
                if self.META.get("QUERY_STRING", "")
                else ""
            ),
        )