def write(self, vals):
        """ Raise UserError with a meaningful message instead of letting the
        uniqueness constraint raise an SQL error. To check uniqueness we have
        to rebuild pairs of names / domains to validate, taking into account
        that a void alias_domain_id is acceptable (but also raises for
        uniqueness).
        """
        alias_names, alias_domains = [], []
        if 'alias_name' in vals:
            vals['alias_name'] = self._sanitize_alias_name(vals['alias_name'])
        if vals.get('alias_name') and self.ids:
            alias_names = [vals['alias_name']] * len(self)
        elif 'alias_name' not in vals and 'alias_domain_id' in vals:
            # avoid checking when writing the same value
            if [vals['alias_domain_id']] != self.alias_domain_id.ids:
                alias_names = self.filtered('alias_name').mapped('alias_name')

        if alias_names:
            tocheck_records = self if vals.get('alias_name') else self.filtered('alias_name')
            if 'alias_domain_id' in vals:
                alias_domains = [self.env['mail.alias.domain'].browse(vals['alias_domain_id'])] * len(tocheck_records)
            else:
                alias_domains = [record.alias_domain_id for record in tocheck_records]
            self._check_unique(alias_names, alias_domains)

        return super().write(vals)