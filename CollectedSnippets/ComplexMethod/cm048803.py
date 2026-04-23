def _sequence_matches_date(self):
        self.ensure_one()
        date = fields.Date.to_date(self[self._sequence_date_field])
        sequence = self[self._sequence_field]

        if not sequence or not date:
            return True

        format_values = self._get_sequence_format_param(sequence)[1]
        sequence_number_reset = self._deduce_sequence_number_reset(sequence)
        date_start, date_end, forced_year_start, forced_year_end = self._get_sequence_date_range(sequence_number_reset)
        year_match = (
            (not format_values["year"] or self._year_match(format_values["year"], forced_year_start or date_start.year))
            and (not format_values["year_end"] or self._year_match(format_values["year_end"], forced_year_end or date_end.year))
        )
        month_match = not format_values['month'] or format_values['month'] == date.month
        return year_match and month_match