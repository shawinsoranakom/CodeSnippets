def _get_preserved_qsl(self, request, preserved_filters):
        query_string = urlsplit(request.build_absolute_uri()).query
        return parse_qsl(query_string.replace(preserved_filters, ""))