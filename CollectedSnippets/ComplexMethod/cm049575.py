def get_suggested_link(self, needle, limit=10):
        current_website = request.website

        matching_pages = []
        limit = None if limit == "no_limit" else int(limit)
        for page in current_website.search_pages(needle, limit):
            matching_pages.append({
                'value': page['loc'],
                'label': 'name' in page and '%s (%s)' % (page['loc'], page['name']) or page['loc'],
            })
        matching_urls = {match['value'] for match in matching_pages}

        matching_last_modified = []
        last_modified_pages = current_website._get_website_pages(order='write_date desc', limit=5)
        for url, name in last_modified_pages.mapped(lambda p: (p.url, p.name)):
            if needle.lower() in name.lower() or needle.lower() in url.lower() and url not in matching_urls:
                matching_last_modified.append({
                    'value': url,
                    'label': '%s (%s)' % (url, name),
                })

        suggested_controllers = []
        for name, url, mod in current_website.get_suggested_controllers():
            if needle.lower() in name.lower() or needle.lower() in url.lower():
                module_sudo = mod and request.env.ref('base.module_%s' % mod, False).sudo()
                icon = mod and '%s' % (module_sudo and module_sudo.icon or mod) or ''
                suggested_controllers.append({
                    'value': url,
                    'icon': icon,
                    'label': '%s (%s)' % (url, name),
                })

        return {
            'matching_pages': sorted(matching_pages, key=lambda o: o['label']),
            'others': [
                dict(title=_('Last modified pages'), values=matching_last_modified),
                dict(title=_('Apps url'), values=suggested_controllers),
            ]
        }