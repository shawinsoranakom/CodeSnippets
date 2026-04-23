def _search(self, domain, offset=0, limit=None, order=None, *, bypass_access=False, **kwargs):
        """ Override that adds specific access rights of mail.activity, to remove
        ids uid could not see according to our custom rules. Please refer to
        :meth:`_check_access` for more details about those rules.

        The method is inspired by what has been done on mail.message. """

        # Rules do not apply to administrator
        if self.env.is_superuser() or bypass_access:
            return super()._search(domain, offset, limit, order, bypass_access=True, **kwargs)

        # retrieve activities and their corresponding res_model, res_id
        # Don't use the ORM to avoid cache pollution
        query = super()._search(domain, offset, limit, order, **kwargs)
        fnames_to_read = ['id', 'res_model', 'res_id', 'user_id']
        rows = self.env.execute_query(query.select(
            *[self._field_to_sql(self._table, fname) for fname in fnames_to_read],
        ))

        # group res_ids by model, and determine accessible records
        # Note: the user can read all activities assigned to him (see at the end of the method)
        model_ids = defaultdict(set)
        for __, res_model, res_id, user_id in rows:
            if user_id != self.env.uid and res_model:
                model_ids[res_model].add(res_id)

        allowed_ids = defaultdict(set)
        for res_model, res_ids in model_ids.items():
            allowed = self.env['mail.message']._filter_records_for_message_operation(
                res_model, res_ids, 'read',
            )
            allowed_ids[res_model] = set(allowed._ids)

        activities = self.browse(
            id_
            for id_, res_model, res_id, user_id in rows
            if user_id == self.env.uid or res_id in allowed_ids[res_model]
        )
        return activities._as_query(order)