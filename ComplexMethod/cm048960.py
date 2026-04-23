def _get_last_sequence_domain(self, relaxed=False):
        """ Returns the SQL WHERE statement to use when fetching the latest record with the same sequence, and its params. """
        self.ensure_one()
        if not self.myinvois_issuance_date:
            return "WHERE FALSE", {}
        where_string = "WHERE name != '/'"
        param = {}

        if not relaxed:
            domain = [('id', '!=', self.id or self._origin.id), ('name', 'not in', ('/', '', False))]
            reference_name = self.sudo().search(domain + [('myinvois_issuance_date', '<=', self.myinvois_issuance_date)], limit=1).name
            if not reference_name:
                reference_name = self.sudo().search(domain, order='myinvois_issuance_date asc', limit=1).name
            sequence_number_reset = self._deduce_sequence_number_reset(reference_name)
            date_start, date_end, *_ = self._get_sequence_date_range(sequence_number_reset)
            where_string += """ AND myinvois_issuance_date BETWEEN %(date_start)s AND %(date_end)s"""
            param['date_start'] = date_start
            param['date_end'] = date_end
            if sequence_number_reset in ('year', 'year_range'):
                param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_monthly_regex.split('(?P<seq>')[0]) + '$'
            elif sequence_number_reset == 'never':
                param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_yearly_regex.split('(?P<seq>')[0]) + '$'

            if param.get('anti_regex'):
                where_string += " AND sequence_prefix !~ %(anti_regex)s "

        return where_string, param