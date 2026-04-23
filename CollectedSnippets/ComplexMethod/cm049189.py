def _compute_display_withholding(self):
        """ The withholding feature should not show on companies which does not contain any withholding taxes. """
        for company, wizards in self.grouped('company_id').items():
            if not company:
                wizards.display_withholding = False
                continue

            withholding_taxes = self.env['account.tax'].search([
                *self.env['account.tax']._check_company_domain(company),
                ('is_withholding_tax_on_payment', '=', True),
            ])
            for wizard in self:
                # To avoid displaying things for nothing, also ensure to only consider withholding taxes matching the payment type.
                payment_type = wizard.payment_type
                if any(line.is_refund for line in wizard.line_ids):
                    # In case of refunds, the payment type won't match the type_tax_use, we need to invert it.
                    if wizard.payment_type == 'inbound':
                        payment_type = 'outbound'
                    else:
                        payment_type = 'inbound'

                wizard_domain = self.env['account.withholding.line']._get_withholding_tax_domain(company=wizard.company_id, payment_type=payment_type)
                wizard_withholding_taxes = withholding_taxes.filtered_domain(wizard_domain)

                will_create_multiple_entry = not wizard.can_edit_wizard or (wizard.can_group_payments and not wizard.group_payment)
                wizard.display_withholding = bool(wizard_withholding_taxes) and not will_create_multiple_entry