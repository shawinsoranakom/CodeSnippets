def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)

        for line, vals in zip(self, vals_list):
            # Don't copy the name of a payment term line.
            if line.display_type == 'payment_term' and line.move_id.is_invoice(True):
                del vals['name']
            # Don't copy restricted fields of notes
            if line.display_type in ('line_section', 'line_subsection', 'line_note'):
                del vals['balance']
                del vals['account_id']
            # Will be recomputed from the price_unit
            if line.display_type == 'product' and line.move_id.is_invoice(True):
                del vals['balance']
            if self.env.context.get('include_business_fields'):
                line._copy_data_extend_business_fields(vals)
        return vals_list