def _deduce_sequence_number_reset(self, name):
        """Detect if the used sequence resets yearly, montly or never.

        :param name: the sequence that is used as a reference to detect the resetting
            periodicity. Typically, it is the last before the one you want to give a
            sequence.
        """
        for regex, ret_val, requirements in [
            (self._sequence_year_range_monthly_regex, 'year_range_month', ['seq', 'year', 'year_end', 'month']),
            (self._sequence_monthly_regex, 'month', ['seq', 'month', 'year']),
            (self._sequence_year_range_regex, 'year_range', ['seq', 'year', 'year_end']),
            (self._sequence_yearly_regex, 'year', ['seq', 'year']),
            (self._sequence_fixed_regex, 'never', ['seq']),
        ]:
            match = re.match(regex, name or '')
            if match:
                groupdict = match.groupdict()
                if (
                    groupdict.get('year_end') and groupdict.get('year')
                    and (
                        len(groupdict['year']) < len(groupdict['year_end'])
                        or self._truncate_year_to_length((int(groupdict['year']) + 1), len(groupdict['year_end'])) != int(groupdict['year_end'])
                    )
                ):
                    # year and year_end are not compatible for range (the difference is not 1)
                    continue
                if all(groupdict.get(req) is not None for req in requirements):
                    return ret_val
        raise ValidationError(_(
            'The sequence regex should at least contain the seq grouping keys. For instance:\n'
            r'^(?P<prefix1>.*?)(?P<seq>\d*)(?P<suffix>\D*?)$'
        ))