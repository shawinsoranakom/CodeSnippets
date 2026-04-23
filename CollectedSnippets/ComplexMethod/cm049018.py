def _shorten_links(self, html, link_tracker_vals, blacklist=None, base_url=None):
        """ Shorten links in an html content. It uses the '/r' short URL routing
        introduced in this module. Using the standard Odoo regex local links are
        found and replaced by global URLs (not including mailto, tel, sms).

        TDE FIXME: could be great to have a record to enable website-based URLs

        :param link_tracker_vals: values given to the created link.tracker, containing
          for example: campaign_id, medium_id, source_id, and any other relevant fields
          like mass_mailing_id in mass_mailing;
        :param list blacklist: list of (local) URLs to not shorten (e.g.
          '/unsubscribe_from_list')
        :param str base_url: either given, either based on config parameter

        :return: updated html
        """
        if not html or is_html_empty(html):
            return html
        base_url = base_url or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        short_schema = base_url + '/r/'

        root_node = lxml.html.fromstring(html)
        link_nodes, urls_and_labels = find_links_with_urls_and_labels(
            root_node, base_url, skip_regex=rf'^{URL_SKIP_PROTOCOL_REGEX}', skip_prefix=short_schema,
            skip_list=blacklist)
        if not link_nodes:
            return html

        links_trackers = self.env['link.tracker'].search_or_create([
            dict(link_tracker_vals, **url_and_label) for url_and_label in urls_and_labels
        ])
        for node, link_tracker in zip(link_nodes, links_trackers):
            node.set("href", link_tracker.short_url)

        new_html = lxml.html.tostring(root_node, encoding="unicode", method="xml")
        if isinstance(html, markupsafe.Markup):
            new_html = markupsafe.Markup(new_html)

        return new_html