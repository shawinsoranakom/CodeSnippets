def _compute_trust_values(self):
        for wizard in self:
            untrusted_payments_count = 0
            untrusted_accounts = self.env['res.partner.bank']
            missing_account_partners = self.env['res.partner']

            total_payment_count = len(wizard.batches)
            if not wizard.group_payment:
                total_amount_values = wizard._get_total_amounts_to_pay(wizard.batches)
                total_payment_count = len(total_amount_values['lines'])

            # Validate batches; if require_partner_bank_account and the account isn't setup and trusted, we do not allow the payment
            for batch in wizard.batches:
                # Use the currently selected partner_bank_id if in edit mode, otherwise use batch account
                batch_account = wizard.partner_bank_id or wizard._get_batch_account(batch)
                if wizard.require_partner_bank_account:
                    if not batch_account:
                        missing_account_partners += batch['lines'].partner_id
                    elif not batch_account.allow_out_payment:
                        untrusted_payments_count += 1 if wizard.group_payment else len(batch['lines'].filtered(lambda line: line in total_amount_values['lines']))
                        untrusted_accounts |= batch_account

            wizard.update({
                'total_payments_amount': total_payment_count,
                'untrusted_payments_count': untrusted_payments_count,
                'untrusted_bank_ids': untrusted_accounts or False,
                'missing_account_partners': missing_account_partners or False,
            })