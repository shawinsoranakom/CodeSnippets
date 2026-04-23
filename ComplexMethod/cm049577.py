def pagenew(self, path="", add_menu=False, template=False, redirect=False, **kwargs):
        # for supported mimetype, get correct default template
        _, ext = os.path.splitext(path)
        ext_special_case = ext != '.html' and ext in EXTENSION_TO_WEB_MIMETYPES

        if not template and ext_special_case:
            default_templ = 'website.default_%s' % ext.lstrip('.')
            if request.env.ref(default_templ, False):
                template = default_templ

        template = template and dict(template=template) or {}
        website_id = kwargs.get('website_id')
        if website_id:
            website = request.env['website'].browse(int(website_id))
            website._force()
        page = request.env['website'].new_page(
            path,
            add_menu=add_menu,
            sections_arch=kwargs.get('sections_arch'),
            page_title=kwargs.get('page_title'),
            **template
        )
        url = page['url']
        # In case the page is created through the 404 "Create Page" button, the
        # URL may use special characters which are slugified on page creation.
        # If that URL is also a menu, we update it accordingly.
        # NB: we don't want to slugify on menu creation as it could redirect
        # towards files (with spaces, apostrophes, etc.).
        menu = request.env['website.menu'].search([('url', '=', '/' + path), ('page_id', '=', False)])
        if menu:
            menu.page_id = page['page_id']

        if redirect:
            if ext_special_case:  # redirect non html pages to backend to edit
                return request.redirect(f"/odoo/ir.ui.view/{page.get('view_id')}")
            return request.redirect(request.env['website'].get_client_action_url(url, True))

        if ext_special_case:
            return json.dumps({'view_id': page.get('view_id')})
        return json.dumps({'url': url})