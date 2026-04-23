def create(self, vals_list):
        vals_list = [vals.copy() for vals in vals_list]
        for vals in vals_list:
            if 'url' not in vals:
                raise ValueError(_('Creating a Link Tracker without URL is not possible'))

            if vals['url'].startswith(('?', '#')):
                raise UserError(_("“%s” is not a valid link, links cannot redirect to the current page.", vals['url']))
            vals['url'] = validate_url(vals['url'])

            if not vals.get('title'):
                vals['title'] = self._get_title_from_url(vals['url'])

            # Prevent the UTMs to be set by the values of UTM cookies
            for (__, fname, __) in self.env['utm.mixin'].tracking_fields():
                if fname not in vals:
                    vals[fname] = False

        links = super(LinkTracker, self).create(vals_list)

        link_tracker_codes = self.env['link.tracker.code']._get_random_code_strings(len(vals_list))

        self.env['link.tracker.code'].sudo().create([
            {
                'code': code,
                'link_id': link.id,
            } for link, code in zip(links, link_tracker_codes)
        ])

        return links