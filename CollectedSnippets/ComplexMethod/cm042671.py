def process_response(
        self, request: Request, response: Response, spider: Spider | None = None
    ) -> Request | Response:
        if (
            request.meta.get("dont_redirect", False)
            or request.method == "HEAD"
            or not isinstance(response, HtmlResponse)
            or urlparse_cached(request).scheme not in {"http", "https"}
        ):
            return response

        interval, url = get_meta_refresh(response, ignore_tags=self._ignore_tags)
        if not url:
            return response
        redirected = self._redirect_request_using_get(request, response, url)
        if urlparse_cached(redirected).scheme not in {"http", "https"}:
            return response
        if cast("float", interval) < self._maxdelay:
            return self._redirect(redirected, request, "meta refresh")
        return response