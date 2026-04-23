def _get_mail_template(self):
        """
        :return: the correct mail template based on the current move type
        """
        template_xmlid = 'account.email_template_edi_invoice'
        if all(move.move_type == 'out_refund' for move in self):
            template_xmlid = 'account.email_template_edi_credit_note'
        elif all(move.move_type == 'in_invoice' and move.journal_id.is_self_billing for move in self):
            template_xmlid = 'account.email_template_edi_self_billing_invoice'
        elif all(move.move_type == 'in_refund' and move.journal_id.is_self_billing for move in self):
            template_xmlid = 'account.email_template_edi_self_billing_credit_note'
        return self.env.ref(template_xmlid)