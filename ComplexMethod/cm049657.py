def _get_sequence_format_param(self, previous):
        """
        Build the format string and values for Croatian invoice numbering.
        Extends the base implementation to inject journal fields into the
        name. Handles both the first number of a period and subsequent ones.
        """
        if self.env.company.country_code != 'HR' or not self.is_sale_document():
            return super()._get_sequence_format_param(previous)

        if not self.journal_id:
            _logger.error("Journal is not set for this invoice.")
            raise ValidationError(self.env._("Journal is not set for this invoice."))
        if self.move_type == 'out_refund' and self.journal_id.refund_sequence:
            premises_label = self.journal_id.l10n_hr_business_premises_label_refund
            device_label = self.journal_id.l10n_hr_issuing_device_label_refund
        else:
            premises_label = self.journal_id.l10n_hr_business_premises_label
            device_label = self.journal_id.l10n_hr_issuing_device_label
        if not premises_label:
            _logger.error("Business premises label is not set on the journal.")
            raise ValidationError(self.env._("Business premises label is not set on the journal."))
        if not device_label:
            _logger.error("Issuing device label is not set on the journal.")
            raise ValidationError(self.env._("Issuing device label is not set on the journal."))

        current_year = datetime.now(pytz.timezone('Europe/Zagreb')).year
        format_values = {
            'code': self.journal_id.code,
            'year': current_year,
            'seq': 1,
            'premises_label': premises_label,
            'device_label': device_label,
            'seq_length': 4,    # Adjust as needed, e.g., 4 for zero-padding
            'year_length': 4,
            'year_end_length': 0,   # Not used in this format
            'month': 0,     # Setting to 0 indicates that month is not used
        }

        # Existing logic for handling previous sequences
        match = re.match(HR_REGEX_STR, previous)
        if not match:
            if previous != self._get_starting_sequence():   # First invoice in the sequence = no need to raise warnings
                _logger.warning("The previous sequence '%s' does not match the expected format. Resetting to initial sequence.", previous)
            _logger.debug("Reset sequence format: %s, Format values: %s", HR_FORMAT_STR, format_values)
            return HR_FORMAT_STR, format_values

        format_values = match.groupdict()
        # Convert 'seq' and 'year' to integers
        try:
            format_values['seq'] = int(format_values.get('seq', '0'))
        except ValueError:
            _logger.error("Invalid sequence number in '%s': seq='%s'", previous, format_values.get('seq'))
            raise ValidationError(self.env._("Invalid sequence number format."))
        try:
            format_values['year'] = int(format_values.get('year', '0'))
        except ValueError:
            _logger.error("Invalid year in '%s': year='%s'", previous, format_values.get('year'))
            raise ValidationError(self.env._("Invalid year format."))

        format_values['code'] = self.journal_id.code
        format_values['premises_label'] = premises_label
        format_values['device_label'] = device_label
        # Handle 'year_end' if it exists, else set to 0
        format_values['year_end'] = int(format_values.get('year_end', '0')) if 'year_end' in format_values else 0
        # Set lengths for dynamic formatting
        format_values['seq_length'] = 4  # Fixed to 4
        format_values['year_length'] = len(str(format_values['year']))
        format_values['year_end_length'] = len(str(format_values['year_end']))  # Ensure 'year_end_length' is always set
        # Add 'month' key with a default value
        format_values['month'] = 0  # Setting to 0 indicates that month is not used

        _logger.debug("Sequence format: %s, Format values: %s", HR_FORMAT_STR, format_values)
        return HR_FORMAT_STR, format_values