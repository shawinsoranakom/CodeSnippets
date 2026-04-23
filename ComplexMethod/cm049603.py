def new_page(self, name=False, add_menu=False, template='website.default_page', ispage=True, namespace=None, page_values=None, menu_values=None, sections_arch=None, page_title=None):
        """ Create a new website page, and assign it a xmlid based on the given one
            :param name: the name of the page
            :param add_menu: if True, add a menu for that page
            :param template: potential xml_id of the page to create
            :param namespace: module part of the xml_id if none, the template module name is used
            :param page_values: default values for the page to be created
            :param menu_values: default values for the menu to be created
            :param sections_arch: HTML content of sections
            :param page_title: if set, it allows using 'name' for the URL and a different title
        """
        if namespace:
            template_module = namespace
        else:
            template_module, _ = template.split('.')
        page_url = '/' + self.env['ir.http']._slugify(name, max_length=1024, path=True)
        page_url = self.get_unique_path(page_url)
        page_key = self.env['ir.http']._slugify(name)
        result = {'url': page_url}

        if not name:
            name = 'Home'
            page_key = 'home'

        template_record = self.env.ref(template)
        arch = template_record.arch
        if sections_arch:
            tree = html.fromstring(arch)
            wrap = tree.xpath('//div[@id="wrap"]')[0]
            for section in html.fromstring(f'<wrap>{sections_arch}</wrap>'):
                wrap.append(section)
            arch = etree.tostring(tree, encoding="unicode")
        website_id = self.env.context.get('website_id')
        key = self.get_unique_key(page_key, template_module)
        view = template_record.copy({'website_id': website_id, 'key': key})

        view.with_context(lang=None).write({
            'arch': arch.replace(template, key),
            'name': page_title or name,
        })
        result['view_id'] = view.id

        if view.arch_fs:
            view.arch_fs = False

        website = self.get_current_website()
        if ispage:
            default_page_values = {
                'url': page_url,
                'website_id': website.id,  # remove it if only one website or not?
                'view_id': view.id,
                'track': True,
            }
            if page_values:
                default_page_values.update(page_values)
            page = self.env['website.page'].create(default_page_values)
            result['page_id'] = page.id
        if add_menu:
            menu = self.env['website.menu'].search([
                ('url', '=', page_url),
                ('website_id', '=', website.id),
            ], limit=1)
            if not menu:
                default_menu_values = {
                    'name': name,
                    'url': page_url,
                    'parent_id': website.menu_id.id,
                    'page_id': page.id,
                    'website_id': website.id,
                }
                if menu_values:
                    default_menu_values.update(menu_values)
                menu = self.env['website.menu'].create(default_menu_values)
            result['menu_id'] = menu.id
        return result