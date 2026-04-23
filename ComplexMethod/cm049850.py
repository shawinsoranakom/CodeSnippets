def _mail_get_alias_domains(self, default_company=False):
        """ Return alias domain linked to each record in self. It is based
        on the company (record's company, environment company) and fallback
        on the first found alias domain if configuration is not correct.

        :param <res.company> default_company: default company in case records
          have no company (or no company field); defaults to env.company;

        :return: for each record ID in self, found <mail.alias.domain>
        """
        record_companies = self._mail_get_companies(default=(default_company or self.env.company))

        # prepare default alias domain, fetch only if necessary
        default_domain = (default_company or self.env.company).alias_domain_id
        all_companies = self.env['res.company'].browse({comp.id for comp in record_companies.values()})
        # early optimization: search only if necessary
        if not default_domain and any(not comp.alias_domain_id for comp in all_companies):
            default_domain = self.env['mail.alias.domain'].search([], limit=1)

        return {
            record.id: (
                record_companies[record.id].alias_domain_id or default_domain
            )
            for record in self
        }