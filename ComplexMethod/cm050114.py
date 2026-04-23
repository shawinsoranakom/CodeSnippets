def _get_seen_list_sms(self):
        """Returns a set of emails already targeted by current mailing/campaign (no duplicates)"""
        self.ensure_one()
        target = self.env[self.mailing_model_real]

        partner_fields = []
        if isinstance(target, self.pool['mail.thread.phone']):
            phone_fields = ['phone_sanitized']
        else:
            phone_fields = [
                fname for fname in target._phone_get_number_fields()
                if fname in target._fields and target._fields[fname].store
            ]
            partner_fields = target._mail_get_partner_fields()
        partner_field = next(
            (fname for fname in partner_fields if target._fields[fname].store and target._fields[fname].type == 'many2one'),
            False
        )
        if not phone_fields and not partner_field:
            raise UserError(_("Unsupported %s for mass SMS", self.mailing_model_id.name))

        query = """
            SELECT %(select_query)s
              FROM mailing_trace trace
              JOIN %(target_table)s target ON (trace.res_id = target.id)
              %(join_add_query)s
             WHERE (%(where_query)s)
               AND trace.mass_mailing_id = %%(mailing_id)s
               AND trace.model = %%(target_model)s
        """
        if phone_fields:
            # phone fields are checked on target mailed model
            select_query = 'target.id, ' + ', '.join('target.%s' % fname for fname in phone_fields)
            where_query = ' OR '.join('target.%s IS NOT NULL' % fname for fname in phone_fields)
            join_add_query = ''
        else:
            # phone fields are checked on res.partner model
            partner_phone_fields = ['phone']
            select_query = 'target.id, ' + ', '.join('partner.%s' % fname for fname in partner_phone_fields)
            where_query = ' OR '.join('partner.%s IS NOT NULL' % fname for fname in partner_phone_fields)
            join_add_query = 'JOIN res_partner partner ON (target.%s = partner.id)' % partner_field

        query = query % {
            'select_query': select_query,
            'where_query': where_query,
            'target_table': target._table,
            'join_add_query': join_add_query,
        }
        params = {'mailing_id': self.id, 'target_model': self.mailing_model_real}
        self.env.cr.execute(query, params)
        query_res = self.env.cr.fetchall()
        seen_list = set(number for item in query_res for number in item[1:] if number)
        seen_ids = set(item[0] for item in query_res)
        _logger.info("Mass SMS %s targets %s: already reached %s SMS", self, target._name, len(seen_list))
        return list(seen_ids), list(seen_list)