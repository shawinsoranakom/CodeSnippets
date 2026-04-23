def _compute_new_values(self):
        """Compute the proposed new values.

        Sets a json string on new_values representing a dictionary thats maps account.move
        ids to a dictionary containing the name if we execute the action, and information
        relative to the preview widget.
        """
        def _get_move_key(move_id):
            company = move_id.company_id
            date_start, date_end = get_fiscal_year(move_id.date, day=company.fiscalyear_last_day, month=int(company.fiscalyear_last_month))
            if self.sequence_number_reset == 'year':
                return move_id.date.year
            elif self.sequence_number_reset == 'year_range':
                return "%s-%s" % (date_start.year, date_end.year)
            elif self.sequence_number_reset == 'year_range_month':
                return "%s-%s/%s" % (date_start.year, date_end.year, move_id.date.month)
            elif self.sequence_number_reset == 'month':
                return (move_id.date.year, move_id.date.month)
            return 'default'

        self.new_values = "{}"
        for record in self.filtered('first_name'):
            moves_by_period = defaultdict(lambda: record.env['account.move'])
            for move in record.move_ids._origin:  # Sort the moves by period depending on the sequence number reset
                moves_by_period[_get_move_key(move)] += move

            seq_format, format_values = record.move_ids[0]._get_sequence_format_param(record.first_name)
            sequence_number_reset = record.move_ids[0]._deduce_sequence_number_reset(record.first_name)

            new_values = {}
            for j, period_recs in enumerate(moves_by_period.values()):
                # compute the new values period by period
                date_start, date_end, forced_year_start, forced_year_end = period_recs[0]._get_sequence_date_range(sequence_number_reset)
                for move in period_recs:
                    new_values[move.id] = {
                        'id': move.id,
                        'current_name': move.name,
                        'state': move.state,
                        'date': format_date(self.env, move.date),
                        'server-date': str(move.date),
                        'server-year-start-date': str(date_start),
                    }

                new_name_list = [seq_format.format(**{
                    **format_values,
                    'month': date_start.month,
                    'year_end': (forced_year_end or date_end.year) % (10 ** format_values['year_end_length']),
                    'year': (forced_year_start or date_start.year) % (10 ** format_values['year_length']),
                    'seq': i + (format_values['seq'] if j == (len(moves_by_period) - 1) else 1),
                }) for i in range(len(period_recs))]

                # For all the moves of this period, assign the name by increasing initial name
                for move, new_name in zip(period_recs.sorted(lambda m: (m.sequence_prefix, m.sequence_number)), new_name_list):
                    new_values[move.id]['new_by_name'] = new_name
                # For all the moves of this period, assign the name by increasing date
                for move, new_name in zip(period_recs.sorted(lambda m: (m.date, m.name or "", m.id)), new_name_list):
                    new_values[move.id]['new_by_date'] = new_name

            record.new_values = json.dumps(new_values)