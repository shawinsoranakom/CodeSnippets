def process_response(self, request, response):
        # It's too late to prevent an unsafe request with a 412 response, and
        # for a HEAD request, the response body is always empty so computing
        # an accurate ETag isn't possible.
        if request.method != "GET":
            return response

        if self.needs_etag(response) and not response.has_header("ETag"):
            set_response_etag(response)

        etag = response.get("ETag")
        last_modified = response.get("Last-Modified")
        last_modified = last_modified and parse_http_date_safe(last_modified)

        if etag or last_modified:
            return get_conditional_response(
                request,
                etag=etag,
                last_modified=last_modified,
                response=response,
            )

        return response