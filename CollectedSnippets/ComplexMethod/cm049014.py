def _compute_redirected_url(self):
        """Compute the URL to which we will redirect the user.

        By default, add UTM values as GET parameters. But if the system parameter
        `link_tracker.no_external_tracking` is set, we add the UTM values in the URL
        *only* for URLs that redirect to the local website (base URL).
        """
        no_external_tracking = self.env['ir.config_parameter'].sudo().get_param('link_tracker.no_external_tracking')

        for tracker in self:
            base_domain = urls.url_parse(tracker.get_base_url()).netloc
            parsed = urls.url_parse(tracker.url)
            if no_external_tracking and parsed.netloc and parsed.netloc != base_domain:
                tracker.redirected_url = parsed.to_url()
                continue

            query = parsed.decode_query()
            for key, field_name, _cook in self.env['utm.mixin'].tracking_fields():
                field = self._fields[field_name]
                attr = tracker[field_name]
                if field.type == 'many2one':
                    attr = attr.name
                if attr:
                    query[key] = attr

            query = urls.url_encode(query)
            # '...' is detected as malicious by some nginx
            # configuration, encoding it solve the issue
            query = query.replace('...', '%2E%2E%2E')
            tracker.redirected_url = parsed.replace(query=query).to_url()