def _handle_error(cls, exception):
        response = super()._handle_error(exception)

        is_frontend_request = bool(getattr(request, 'is_frontend', False))
        if not is_frontend_request or not isinstance(response, HTTPException):
            # neither handle backend requests nor plain responses
            return response

        # minimal setup to serve frontend pages
        if not request.env.uid:
            cls._auth_method_public()
        cls._handle_debug()
        cls._frontend_pre_dispatch()
        request.params = request.get_http_params()

        code, values = cls._get_exception_code_values(exception)

        request.env.cr.rollback()
        if code in (404, 403):
            try:
                response = cls._serve_fallback()
                if response:
                    cls._post_dispatch(response)
                    return response
            except werkzeug.exceptions.Forbidden:
                # Rendering does raise a Forbidden if target is not visible.
                pass # Use default error page handling.
        elif code == 500:
            values = cls._get_values_500_error(request.env, values, exception)
        try:
            code, html = cls._get_error_html(request.env, code, values)
        except Exception:
            _logger.exception("Couldn't render a template for http status %s", code)
            code, html = 418, request.env['ir.ui.view']._render_template('http_routing.http_error', values)

        response = Response(html, status=code, content_type='text/html;charset=utf-8')
        cls._post_dispatch(response)
        return response