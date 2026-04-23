def _setup_base_lines(self, vals):
        base_lines = vals['base_lines']
        company = vals['company']

        for base_line in base_lines:
            # Allow retrieving the invoice line from the base_line.
            base_line['_invoice_line'] = base_line['record']
            line_name = base_line['record'] and base_line['record'].name
            base_line['_line_name'] = line_name and line_name.replace('\n', ' ')

            # Allow retrieving some custom values coming from manipulations of base lines.
            base_line['_ubl_values'] = {
                'recycling_contribution_taxes_data': [],
            }

        # Manage taxes for recycling contribution such as RECUPEL / AUVIBEL.
        self._dispatch_base_lines_recycling_contribution_taxes(base_lines, company, vals)

        # Manage taxes for emptying.
        base_lines = self._turn_emptying_taxes_as_new_base_lines(base_lines, company, vals)

        # Extract cash rounding lines.
        vals['base_lines'] = [base_line for base_line in base_lines if base_line['special_type'] != 'cash_rounding']
        vals['cash_rounding_base_lines'] = [base_line for base_line in base_lines if base_line['special_type'] == 'cash_rounding']