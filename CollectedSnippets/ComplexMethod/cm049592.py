def _register_website_track(cls, response):
        if request.env['ir.http'].is_a_bot():
            return False
        if getattr(response, 'status_code', 0) != 200 or request.httprequest.headers.get('X-Disable-Tracking') == '1':
            return False
        template = False
        if hasattr(response, '_cached_page'):
            website_page, template = response._cached_page, response._cached_view_id
        elif hasattr(response, 'qcontext'):  # classic response
            main_object = response.qcontext.get('main_object')
            website_page = getattr(main_object, '_name', False) == 'website.page' and main_object
            template = response.qcontext.get('response_template')
            if isinstance(template, str) and '.' not in template:
                template = 'website.%s' % template

        if template and not request.env.cr.readonly and request.env['ir.ui.view']._get_cached_template_info(template)['track']:
            request.env['website.visitor']._handle_webpage_dispatch(website_page)

        return False