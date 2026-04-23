def _create_payment_vals_from_batch(self, batch_result):
        batch_values = self._get_wizard_values_from_batch(batch_result)

        if batch_values['payment_type'] == 'inbound':
            partner_bank_id = self.journal_id.bank_account_id.id
        else:
            partner_bank_id = batch_result['payment_values']['partner_bank_id']

        payment_method_line = self.payment_method_line_id

        if batch_values['payment_type'] != payment_method_line.payment_type:
            payment_method_line = self.journal_id._get_available_payment_method_lines(batch_values['payment_type'])[:1]

        payment_vals = {
            'date': self.payment_date,
            'amount': batch_values['source_amount_currency'],
            'payment_type': batch_values['payment_type'],
            'partner_type': batch_values['partner_type'],
            'memo': self._get_communication(batch_result['lines']),
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': batch_values['source_currency_id'],
            'partner_id': batch_values['partner_id'],
            'payment_method_line_id': payment_method_line.id,
            'destination_account_id': batch_result['lines'][0].account_id.id,
            'write_off_line_vals': [],
        }

        # In case it is false, we don't add it to the create vals so that
        # _compute_partner_bank_id is executed at payment creation
        if partner_bank_id:
            payment_vals['partner_bank_id'] = partner_bank_id

        total_amount_values = self._get_total_amounts_to_pay([batch_result])
        total_amount = total_amount_values['amount_by_default']
        currency = self.env['res.currency'].browse(batch_values['source_currency_id'])
        if total_amount_values['epd_applied']:
            payment_vals['amount'] = total_amount

            epd_aml_values_list = []
            for aml in batch_result['lines']:
                if aml.move_id._is_eligible_for_early_payment_discount(currency, self.payment_date):
                    epd_aml_values_list.append({
                        'aml': aml,
                        'amount_currency': -aml.amount_residual_currency,
                        'balance': currency._convert(-aml.amount_residual_currency, aml.company_currency_id, self.company_id, self.payment_date),
                    })

            open_amount_currency = (batch_values['source_amount_currency'] - total_amount) * (-1 if batch_values['payment_type'] == 'outbound' else 1)
            open_balance = currency._convert(open_amount_currency, aml.company_currency_id, self.company_id, self.payment_date)
            early_payment_values = self.env['account.move']\
                ._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list, open_balance)
            for aml_values_list in early_payment_values.values():
                payment_vals['write_off_line_vals'] += aml_values_list

        return payment_vals