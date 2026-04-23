def _create_misc_operation(tax, tax_field):
            with Form(self.env['account.move'], view='account.view_move_form') as move_form:
                for line_field in ('debit', 'credit'):
                    line_amount = tax_field == line_field and 1000 or 1150
                    with move_form.line_ids.new() as line_form:
                        line_form.name = '%s_line' % line_field
                        line_form.account_id = self.company_data['default_account_revenue']
                        line_form.debit = line_field == 'debit' and line_amount or 0
                        line_form.credit = line_field == 'credit' and line_amount or 0

                        if tax_field == line_field:
                            line_form.tax_ids.clear()
                            line_form.tax_ids.add(tax)

            return move_form.save()