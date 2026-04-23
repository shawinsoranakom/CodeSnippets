def _notify_get_reply_to_batch(self, defaults=None, author_ids=None):
        """ Batch-enabled version of '_notify_get_reply_to' where default and
        author_id may be different / record. This one exist mainly for batch
        intensive computation like composer in mass mode, where email configuration
        is different / record due to dynamic rendering.

        :param dict defaults: default / record ID;
        :param dict author_ids: author ID / record ID;
        """
        _records = self
        model = _records._name if _records and _records._name != 'mail.thread' else False
        res_ids = _records.ids if _records and model else []
        _res_ids = res_ids or [False]  # always have a default value located in False
        _records_sudo = _records.sudo()
        if defaults is None:
            defaults = dict.fromkeys(_res_ids, False)
        if author_ids is None:
            author_ids = dict.fromkeys(_res_ids, False)

        # sanity check
        if set(defaults.keys()) != set(_res_ids):
            raise ValueError(f'Invalid defaults, keys {defaults.keys()} does not match recordset IDs {_res_ids}')
        if set(author_ids.keys()) != set(_res_ids):
            raise ValueError(f'Invalid author_ids, keys {author_ids.keys()} does not match recordset IDs {_res_ids}')

        # group ids per company
        if res_ids:
            company_to_res_ids = defaultdict(list)
            record_ids_to_company = _records_sudo._mail_get_companies(default=self.env.company)
            for record_id, company in record_ids_to_company.items():
                company_to_res_ids[company].append(record_id)
        else:
            company_to_res_ids = {self.env.company: _res_ids}
            record_ids_to_company = {_res_id: self.env.company for _res_id in _res_ids}

        # begin with aliases (independent from company, alias_domain_id on alias wins)
        reply_to_email = {}
        if model and res_ids:
            mail_aliases = self.env['mail.alias'].sudo().search([
                ('alias_domain_id', '!=', False),
                ('alias_parent_model_id.model', '=', model),
                ('alias_parent_thread_id', 'in', res_ids),
                ('alias_name', '!=', False)
            ])
            # take only first found alias for each thread_id, to match order (1 found -> limit=1 for each res_id)
            for alias in mail_aliases:
                reply_to_email.setdefault(alias.alias_parent_thread_id, alias.alias_full_name)

        # continue with company alias
        left_ids = set(_res_ids) - set(reply_to_email)
        if left_ids:
            for company, record_ids in company_to_res_ids.items():
                # left ids: use catchall defined on company alias domain
                if company.catchall_email:
                    left_ids = set(record_ids) - set(reply_to_email)
                    if left_ids:
                        reply_to_email.update({rec_id: company.catchall_email for rec_id in left_ids})

        # compute name of reply-to ("Company Document" <alias@domain>)
        reply_to_formatted = dict(defaults)
        for res_id, record_reply_to in reply_to_email.items():
            reply_to_formatted[res_id] = self._notify_get_reply_to_formatted_email(
                record_reply_to,
                author_id=author_ids[res_id],
            )

        return reply_to_formatted