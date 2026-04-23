def _prepare_values(self, limit=None, search_domain=None, **options):
        """Gets the data and returns it the right format for render."""
        self and self.ensure_one()

        model_name = options.get('res_model') or self.filter_id.sudo().model_id
        website_filter_models = list({
            website_filter.action_server_id.model_id.model if website_filter.action_server_id
            else website_filter.filter_id.model_id
            for website_filter in self.env['website.snippet.filter'].search([])
        })
        if model_name and model_name not in website_filter_models:
            return []
        res_id = options.get('res_id')
        # The "limit" field is there to prevent loading an arbitrary number of
        # records asked by the client side. This here makes sure you can always
        # load at least 16 records as it is what the editor allows.
        max_limit = max(self.limit, 16)
        limit = limit and min(limit, max_limit) or max_limit
        single_record_filter = limit == 1 and model_name and res_id

        # Either a multi-record filter is provided, or a single record is specified.
        if self.filter_id or single_record_filter:
            if not single_record_filter:
                filter_sudo = self.filter_id.sudo()
                domain = Domain(filter_sudo._get_eval_domain())
                if 'website_id' in self.env[model_name]:
                    domain &= self.env['website'].get_current_website().website_domain()
                if 'company_id' in self.env[model_name]:
                    website = self.env['website'].get_current_website()
                    domain &= Domain('company_id', 'in', [False, website.company_id.id])
                if 'is_published' in self.env[model_name]:
                    domain &= Domain('is_published', '=', True)
                if search_domain:
                    search_domain = Domain(search_domain)
                    domain &= search_domain
            try:
                records = self.env[model_name].sudo(False).with_context(**literal_eval(filter_sudo.context)).search(
                    domain,
                    order=','.join(literal_eval(filter_sudo.sort)) or None,
                    limit=limit
                ) if not single_record_filter else self.env[model_name].sudo(False).search([('id', '=', res_id)], limit=1)
                return self._filter_records_to_values(records.sudo(), res_model=model_name)
            except MissingError:
                if not single_record_filter:
                    _logger.warning("The provided domain %s in 'ir.filters' generated a MissingError in '%s'", domain, self._name)
                return []
        elif self.action_server_id:
            try:
                return self.action_server_id.with_context(
                    dynamic_filter=self,
                    limit=limit,
                    search_domain=search_domain,
                ).sudo().run() or []
            except MissingError:
                _logger.warning("The provided domain %s in 'ir.actions.server' generated a MissingError in '%s'", search_domain, self._name)
                return []