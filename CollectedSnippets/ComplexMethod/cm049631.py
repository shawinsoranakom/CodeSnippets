def save(self, website_id, data):
        def replace_id(old_id, new_id):
            for menu in data['data']:
                if menu['id'] == old_id:
                    menu['id'] = new_id
                if menu['parent_id'] == old_id:
                    menu['parent_id'] = new_id
        to_delete = data.get('to_delete')
        if to_delete:
            self.browse(to_delete).unlink()
        for menu in data['data']:
            mid = menu['id']
            # new menu are prefixed by new-
            if isinstance(mid, str):
                new_menu = self.create({'name': menu['name'], 'website_id': website_id})
                replace_id(mid, new_menu.id)
        for menu in data['data']:
            menu_id = self.browse(menu['id'])
            # Check if the url match a website.page (to set the m2o relation),
            # except if the menu url contains '#', we then unset the page_id
            if '#' in menu['url']:
                # Multiple case possible
                # 1. `#` => menu container (dropdown, ..)
                # 2. `#top` or `#bottom` => special anchors valid for any page
                # 3. `#anchor` => anchor on current page
                # 4. `/url#something` => valid internal URL
                # 5. https://google.com#smth => valid external URL
                if menu_id.page_id:
                    menu_id.page_id = None
                if request and menu['url'].startswith('#') and len(menu['url']) > 1 and \
                        menu['url'] not in ['#top', '#bottom']:
                    # Working on case 2.: prefix anchor with referer URL
                    referer_url = werkzeug.urls.url_parse(request.httprequest.headers.get('Referer', '')).path
                    menu['url'] = referer_url + menu['url']
            else:
                domain = self.env["website"].browse(website_id).website_domain() & (
                    Domain("url", "=", menu["url"])
                    | Domain("url", "=", "/" + menu["url"])
                )
                page = self.env["website.page"].search(domain, limit=1)
                if page:
                    menu['page_id'] = page.id
                    menu['url'] = page.url
                    if isinstance(menu.get('parent_id'), str):
                        # Avoid failure if parent_id is sent as a string from a customization.
                        menu['parent_id'] = int(menu['parent_id'])
                elif menu_id.page_id:
                    try:
                        # a page shouldn't have the same url as a controller
                        self.env['ir.http']._match(menu['url'])
                        menu_id.page_id = None
                    except werkzeug.exceptions.NotFound:
                        menu_id.page_id.write({'url': menu['url']})
            menu_id.write(menu)

        return True