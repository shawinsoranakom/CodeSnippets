def write(self, vals):
        """ Split writable fields of mail.alias and other fields alias fields will
        write with sudo and the other normally. Also handle alias_domain_id
        update. If alias does not exist and we try to set a name, create the
        alias automatically. """
        # create missing aliases
        if vals.get('alias_name'):
            alias_create_values = [
                dict(
                    record._alias_get_creation_values(),
                    alias_name=self.env['mail.alias']._sanitize_alias_name(vals['alias_name']),
                )
                for record in self.filtered(lambda rec: not rec.alias_id)
            ]
            if alias_create_values:
                aliases = self.env['mail.alias'].sudo().create(alias_create_values)
                for record, alias in zip(self.filtered(lambda rec: not rec.alias_id), aliases):
                    record.alias_id = alias.id

        alias_vals, record_vals = self._alias_filter_fields(vals, filters=self.ALIAS_WRITEABLE_FIELDS)
        if record_vals:
            super().write(record_vals)

        # synchronize alias domain if company environment changed
        company_fname = self._mail_get_company_field()
        if company_fname in vals:
            alias_domain_values = self.filtered('alias_id')._alias_get_alias_domain_id()
            for record, alias_domain_id in alias_domain_values.items():
                record.sudo().alias_domain_id = alias_domain_id.id

        if alias_vals and (record_vals or self.browse().has_access('write')):
            self.mapped('alias_id').sudo().write(alias_vals)

        return True