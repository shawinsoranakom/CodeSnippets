def _get_subscription_data(self, doc_data, pids, include_pshare=False, include_active=False):
        """ Private method allowing to fetch follower data from several documents of a given model.
        MailFollowers can be filtered given partner IDs and channel IDs.

        :param doc_data: list of pair (res_model, res_ids) that are the documents from which we
          want to have subscription data;
        :param pids: optional partner to filter; if None take all, otherwise limitate to pids
        :param include_pshare: optional join in partner to fetch their share status
        :param include_active: optional join in partner to fetch their active flag

        :return: list of followers data which is a list of tuples containing
          follower ID,
          document ID,
          partner ID,
          followed subtype IDs,
          share status of partner (returned only if include_pshare is True)
          active flag status of partner (returned only if include_active is True)
        """
        self.env['mail.followers'].flush_model(['partner_id', 'res_id', 'res_model', 'subtype_ids'])
        self.env['res.partner'].flush_model(['active', 'partner_share'])
        # base query: fetch followers of given documents
        where_clause = ' OR '.join(['fol.res_model = %s AND fol.res_id IN %s'] * len(doc_data))
        where_params = list(itertools.chain.from_iterable((rm, tuple(rids)) for rm, rids in doc_data))

        # additional: filter on optional pids
        sub_where = []
        if pids:
            sub_where += ["fol.partner_id IN %s"]
            where_params.append(tuple(pids))
        elif pids is not None:
            sub_where += ["fol.partner_id IS NULL"]
        if sub_where:
            where_clause += "AND (%s)" % " OR ".join(sub_where)

        query = """
SELECT fol.id, fol.res_id, fol.partner_id, array_agg(subtype.id)%s%s
FROM mail_followers fol
%s
LEFT JOIN mail_followers_mail_message_subtype_rel fol_rel ON fol_rel.mail_followers_id = fol.id
LEFT JOIN mail_message_subtype subtype ON subtype.id = fol_rel.mail_message_subtype_id
WHERE %s
GROUP BY fol.id%s%s""" % (
            ', partner.partner_share' if include_pshare else '',
            ', partner.active' if include_active else '',
            'LEFT JOIN res_partner partner ON partner.id = fol.partner_id' if (include_pshare or include_active) else '',
            where_clause,
            ', partner.partner_share' if include_pshare else '',
            ', partner.active' if include_active else ''
        )
        self.env.cr.execute(query, tuple(where_params))
        return self.env.cr.fetchall()