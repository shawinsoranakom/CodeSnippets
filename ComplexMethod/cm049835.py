def _search(self, domain, offset=0, limit=None, order=None, *, bypass_access=False, **kwargs):
        """ Override that adds specific access rights of mail.message, to remove
        ids uid could not see according to our custom rules. Please refer to
        _check_access() for more details about those rules.

        Non employees users see only message with subtype, and cannot see
        internal messages, either coming from message 'is_internal' flag,
        subtype 'internal' flag, or being pure logs (no subtype). See
        `_get_search_domain_share` which generates the domain.

        After having received ids of a classic search, keep only:
        - if author_id == pid, uid is the author, OR
        - uid belongs to a notified channel, OR
        - uid is in the specified recipients, OR
        - uid has a notification on the message, OR
        - uid has acces to the message linked document for messages that are not
          'user_notification'
        - otherwise: remove the id
        """
        # Rules do not apply to administrator
        if self.env.is_superuser() or bypass_access:
            return super()._search(domain, offset, limit, order, bypass_access=True, **kwargs)

        # Non-employee see only messages with a subtype and not internal
        if not self.env.user._is_internal():
            domain = self._get_search_domain_share() & Domain(domain)

        # make the search query with the default rules
        query = super()._search(domain, offset, limit, order, **kwargs)

        # retrieve matching records and determine which ones are truly accessible
        self.flush_model(['model', 'res_id', 'author_id', 'message_type', 'partner_ids'])
        self.env['mail.notification'].flush_model(['mail_message_id', 'res_partner_id'])

        pid = self.env.user.partner_id.id
        ids = []
        allowed_ids = set()
        model_ids = defaultdict(lambda: defaultdict(set))

        rel_alias = query.make_alias(self._table, 'partner_ids')
        query.add_join("LEFT JOIN", rel_alias, 'mail_message_res_partner_rel', SQL(
            "%s = %s AND %s = %s",
            SQL.identifier(self._table, 'id'),
            SQL.identifier(rel_alias, 'mail_message_id'),
            SQL.identifier(rel_alias, 'res_partner_id'),
            pid,
        ))
        notif_alias = query.make_alias(self._table, 'notification_ids')
        query.add_join("LEFT JOIN", notif_alias, 'mail_notification', SQL(
            "%s = %s AND %s = %s",
            SQL.identifier(self._table, 'id'),
            SQL.identifier(notif_alias, 'mail_message_id'),
            SQL.identifier(notif_alias, 'res_partner_id'),
            pid,
        ))
        self.env.cr.execute(query.select(
            SQL.identifier(self._table, 'id'),
            SQL.identifier(self._table, 'model'),
            SQL.identifier(self._table, 'res_id'),
            SQL.identifier(self._table, 'author_id'),
            SQL.identifier(self._table, 'message_type'),
            SQL(
                "COALESCE(%s, %s)",
                SQL.identifier(rel_alias, 'res_partner_id'),
                SQL.identifier(notif_alias, 'res_partner_id'),
            ),
        ))
        for id_, model, res_id, author_id, message_type, partner_id in self.env.cr.fetchall():
            ids.append(id_)
            if author_id == pid:
                allowed_ids.add(id_)
            elif partner_id == pid:
                allowed_ids.add(id_)
            elif model and res_id and message_type != 'user_notification':
                model_ids[model][res_id].add(id_)

        allowed_ids.update(self._find_allowed_doc_ids(model_ids))
        allowed = self.browse(id_ for id_ in ids if id_ in allowed_ids)
        return allowed._as_query(order)