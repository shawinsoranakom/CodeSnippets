def write(self, vals):
        for page in self:
            website_id = False
            if vals.get('website_id') or page.website_id:
                website_id = vals.get('website_id') or page.website_id.id

            # If URL has been edited, slug it
            if 'url' in vals:
                url = vals['url'] or ''
                url = '/' + self.env['ir.http']._slugify(url, max_length=1024, path=True)
                if page.url != url:
                    url = self.env['website'].with_context(website_id=website_id).get_unique_path(url)
                    page.menu_ids.write({'url': url})
                    # Sync website's homepage URL
                    website = self.env['website'].get_current_website()
                    page_url_normalized = {'homepage_url': page.url}
                    website._handle_homepage_url(page_url_normalized)
                    if website.homepage_url == page_url_normalized['homepage_url']:
                        website.homepage_url = url
                vals['url'] = url

            # If name has changed, check for key uniqueness
            if 'name' in vals and page.name != vals['name']:
                vals['key'] = self.env['website'].with_context(website_id=website_id).get_unique_key(self.env['ir.http']._slugify(vals['name'] or ''))
            if 'visibility' in vals:
                if vals['visibility'] != 'restricted_group':
                    vals['group_ids'] = False

        if 'url' in vals or 'visibility' in vals or 'group_ids' in vals:
            self.env.registry.clear_cache('templates')   # Clear cache because the response depends on the path and the rendering of the view changes.

        return super().write(vals)