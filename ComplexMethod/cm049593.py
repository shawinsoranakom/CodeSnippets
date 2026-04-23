def _serve_page(cls):
        req_page = request.httprequest.path
        WebsitePage = request.env['website.page'].sudo()
        page_info = WebsitePage._get_page_info(request)

        # redirect to the right url
        if page_info and page_info['url'] != req_page:
            logger.info("Page %r not found, redirecting to existing page %r", req_page, page_info['url'])
            return request.redirect(page_info['url'])

        # redirect without trailing /
        if not page_info and req_page != "/" and req_page.endswith("/"):
            # mimick `_postprocess_args()` redirect
            path = request.httprequest.path[:-1]
            if request.lang != cls._get_default_lang():
                path = '/' + request.lang.url_code + path
            if request.httprequest.query_string:
                path += '?' + request.httprequest.query_string.decode('utf-8')
            return request.redirect(path, code=301)

        if page_info:
            return WebsitePage.browse(page_info['id'])._get_response(request)

        return False