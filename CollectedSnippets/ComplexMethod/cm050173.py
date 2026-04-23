def print_checks(self):
        """ Check that the recordset is valid, set the payments state to sent and call print_checks() """
        # Since this method can be called via a client_action_multi, we need to make sure the received records are what we expect
        valid_payments = self.filtered(lambda r: r.payment_method_line_id.code == 'check_printing' and not r.is_sent)

        if len(valid_payments) == 0:
            raise UserError(_("Payments to print as a checks must have 'Check' selected as payment method and "
                              "not have already been reconciled"))
        if any(payment.journal_id != valid_payments[0].journal_id for payment in valid_payments):
            raise UserError(_("In order to print multiple checks at once, they must belong to the same bank journal."))

        if not valid_payments[0].journal_id.check_manual_sequencing:
            # The wizard asks for the number printed on the first pre-printed check
            # so payments are attributed the number of the check the'll be printed on.
            self.env.cr.execute("""
                  SELECT payment.check_number
                    FROM account_payment payment
                   WHERE payment.journal_id = %(journal_id)s
                     AND payment.check_number IS NOT NULL
                ORDER BY payment.check_number::BIGINT DESC
                   LIMIT 1
            """, {
                'journal_id': self.journal_id.id,
            })
            last_check_number = (self.env.cr.fetchone() or (False,))[0]
            number_len = len(last_check_number or "")
            next_check_number = f'{int(last_check_number) + 1:0{number_len}}'

            return {
                'name': _('Print Pre-numbered Checks'),
                'type': 'ir.actions.act_window',
                'res_model': 'print.prenumbered.checks',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'payment_ids': valid_payments.ids,
                    'default_next_check_number': next_check_number,
                }
            }
        else:
            valid_payments.filtered(lambda r: r.state == 'draft').action_post()
            return valid_payments.do_print_checks()