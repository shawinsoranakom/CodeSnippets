def _get_last_sequence_domain(self, relaxed=False):
        #pylint: disable=sql-injection
        # EXTENDS account sequence.mixin
        self.ensure_one()
        if not self.date or not self.journal_id:
            return "WHERE FALSE", {}
        where_string = "WHERE journal_id = %(journal_id)s AND name != '/'"
        param = {'journal_id': self.journal_id.id}
        is_payment = self.origin_payment_id or self.env.context.get('is_payment')

        if not relaxed:
            domain = [('journal_id', '=', self.journal_id.id), ('id', '!=', self.id or self._origin.id), ('name', 'not in', ('/', '', False))]
            if self.journal_id.refund_sequence:
                refund_types = ('out_refund', 'in_refund')
                domain += [('move_type', 'in' if self.move_type in refund_types else 'not in', refund_types)]
            if self.journal_id.payment_sequence:
                domain += [('origin_payment_id', '!=' if is_payment else '=', False)]
            if self.journal_id.is_self_billing:
                if self.partner_id:
                    domain += [('commercial_partner_id', '=', self.partner_id.commercial_partner_id.id)]
                else:
                    # If the partner id is not set, we can't compute the sequence, so we force a sequence reset.
                    domain += [(0, '=', 1)]
            reference_move_name = self.sudo().search(domain + [('date', '<=', self.date)], order='date desc', limit=1).name
            if not reference_move_name:
                reference_move_name = self.sudo().search(domain, order='date asc', limit=1).name
            sequence_number_reset = self._deduce_sequence_number_reset(reference_move_name)
            date_start, date_end, *_ = self._get_sequence_date_range(sequence_number_reset)
            where_string += """ AND date BETWEEN %(date_start)s AND %(date_end)s"""
            param['date_start'] = date_start
            param['date_end'] = date_end

            # Some regex are catching more sequence formats than we want, so we
            # need to exclude them:
            #
            #                    |                 Regex type                                 |
            # Move Name Format   | Fixed | Yearly | Monthly | Year Range | Year range Monthly |
            # ------------------ | ----- | ------ | ------- | ---------- | ------------------ |
            # Fixed              |   X   |        |         |            |                    |
            # Yearly             |   X   |   X    |         |            |                    |
            # Monthly            |   X   |   X    |    X    |     X      |                    |
            # Year Range         |   X   |   X    |         |     X      |                    |
            # Year range Monthly |   X   |   X    |    X    |     X      |          X         |
            if sequence_number_reset in ('year', 'year_range'):
                param['anti_regex'] = self._make_regex_non_capturing(self._sequence_monthly_regex.split('(?P<seq>')[0]) + '$'
            elif sequence_number_reset == 'never':
                # Excluding yearly will also exclude "monthly", "year range" and
                # "year range monthly"
                param['anti_regex'] = self._make_regex_non_capturing(self._sequence_yearly_regex.split('(?P<seq>')[0]) + '$'

            if param.get('anti_regex') and not self.journal_id.sequence_override_regex and not self.env.context.get('no_anti_regex'):
                where_string += " AND sequence_prefix !~ %(anti_regex)s "

        if self.journal_id.refund_sequence:
            if self.move_type in ('out_refund', 'in_refund'):
                where_string += " AND move_type IN ('out_refund', 'in_refund') "
            else:
                where_string += " AND move_type NOT IN ('out_refund', 'in_refund') "
        elif self.journal_id.payment_sequence:
            if is_payment:
                where_string += " AND origin_payment_id IS NOT NULL "
            else:
                where_string += " AND origin_payment_id IS NULL "

        if self.journal_id.is_self_billing:
            if self.partner_id:
                where_string += " AND commercial_partner_id = %(partner_id)s "
                param['partner_id'] = self.partner_id.commercial_partner_id.id
            else:
                where_string += " AND false "
        return where_string, param