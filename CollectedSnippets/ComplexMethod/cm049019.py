def _shorten_links_text(self, content, link_tracker_vals, blacklist=None, base_url=None):
        """ Shorten links in a string content. Works like ``_shorten_links`` but
        targeting string content, not html.

        :return: updated content
        """
        if not content:
            return content
        base_url = base_url or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        shortened_schema = base_url + '/r/'
        unsubscribe_schema = base_url + '/sms/'
        for original_url in set(re.findall(TEXT_URL_REGEX, content)):
            # don't shorten already-shortened links or links towards unsubscribe page
            if original_url.startswith(shortened_schema) or original_url.startswith(unsubscribe_schema):
                continue
            # support blacklist items in path, like /u/
            parsed = urls.url_parse(original_url, scheme='http')
            if blacklist and any(re.search(item + r'([#?/]|$)', parsed.path) for item in blacklist):
                continue

            create_vals = dict(link_tracker_vals, url=unescape(original_url))
            link = self.env['link.tracker'].search_or_create([create_vals])
            if link.short_url:
                # Ensures we only replace the same link and not a subpart of a longer one, multiple times if applicable
                content = re.sub(re.escape(original_url) + r'(?![\w@:%.+&~#=/-])', link.short_url, content)

        return content