def write(self, vals):
        write_result = super().write(vals)

        # Once website.page has been written, the url might have been modified.
        # We can now create the redirects.
        if 'url' in vals:
            for record in self:
                old_url = record.old_url
                new_url = record.url
                if old_url != new_url:
                    if vals.get('redirect_old_url'):
                        website_id = vals.get('website_id') or record.website_id.id or False
                        self.env['website.rewrite'].create(
                            {
                                'name': vals.get('name') or record.name,
                                'redirect_type': vals.get('redirect_type') or record.redirect_type,
                                'url_from': old_url,
                                'url_to': new_url,
                                'website_id': website_id,
                            }
                        )
                    record.old_url = new_url

        return write_result