def _search(self, domain, offset=0, limit=None, order=None, *, bypass_access=False, **kwargs):
        """ Override that add specific access rights to only get the ids of the messages
        that are scheduled on the records on which the user has mail_post (or read) access
        """
        if self.env.is_superuser() or bypass_access:
            return super()._search(domain, offset, limit, order, bypass_access=True, **kwargs)

        # don't use the ORM to avoid cache pollution
        query = super()._search(domain, offset, limit, order, **kwargs)
        fnames_to_read = ['id', 'model', 'res_id']
        rows = self.env.execute_query(query.select(
            *[self._field_to_sql(self._table, fname) for fname in fnames_to_read],
        ))

        # group res_ids by model and determine accessible records
        model_ids = defaultdict(set)
        for __, model, res_id in rows:
            model_ids[model].add(res_id)

        allowed_ids = defaultdict(set)
        for model, res_ids in model_ids.items():
            records = self.env[model].browse(res_ids)
            operation = getattr(records, '_mail_post_access', 'write')
            if records.has_access(operation):
                allowed_ids[model] = set(records._filtered_access(operation)._ids)

        scheduled_messages = self.browse(
            msg_id
            for msg_id, res_model, res_id in rows
            if res_id in allowed_ids[res_model]
        )

        return scheduled_messages._as_query(order)