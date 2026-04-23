def _l10n_tw_edi_check_before_generate_issue_allowance_json(self):
        self.ensure_one()
        if not self.l10n_tw_edi_ecpay_invoice_id:
            raise UserError(self.env._(
                "You cannot issue an allowance for invoice %(invoice_number)s as it was not sent to Ecpay. ",
                invoice_number=self.name
            ))

        if (self.l10n_tw_edi_is_b2b or self.l10n_tw_edi_refund_agreement_type == "online") and not self.partner_id.email:
            raise UserError(self.env._("Customer email is needed for notification"))

        if not self.l10n_tw_edi_is_b2b and \
                ((self.l10n_tw_edi_allowance_notify_way == "email" and not self.partner_id.email) or (self.l10n_tw_edi_allowance_notify_way == "phone" and not self.partner_id.phone)):
            raise UserError(self.env._("Customer %(notify_way)s is needed for notification",
                                       notify_way=self.l10n_tw_edi_allowance_notify_way))