def _generate_pos_order_invoice(self):
        # EXTENDS 'point_of_sale'
        if self.company_id._l10n_my_edi_enabled():
            for order in self:
                if order._get_active_consolidated_invoice():
                    raise UserError(order.env._("This order has been included in a consolidated invoice and cannot be invoiced separately."))

                refunded_consolidated_invoice = order.refunded_order_id and order.refunded_order_id._get_active_consolidated_invoice()
                refunding_consolidated_invoice = refunded_consolidated_invoice and refunded_consolidated_invoice.myinvois_state in ["in_progress", "valid", "rejected"]
                # We can skip this check when refunding a consolidated invoice, since the customer in the XML is fixed.
                if not refunding_consolidated_invoice:
                    partner = order.partner_id
                    if (
                        not partner.l10n_my_identification_type
                        or not partner.l10n_my_identification_number
                    ):
                        raise UserError(order.env._("You must set the identification information on the commercial partner."))
                    if not partner._l10n_my_edi_get_tin_for_myinvois():
                        raise UserError(order.env._("You must set a TIN number on the commercial partner."))

            # We need to wait for MyInvois to give us a code during submission before generating the PDF file.
            # To do so, we will invoice without PDF, send and only then generate the PDF file.
            action_values = super(PosOrder, self.with_context(generate_pdf=False))._generate_pos_order_invoice()

            # At this point we don't want to raise anymore, if there are issues it'll be logged on the invoice, and we will
            # move on.
            self.account_move.action_l10n_my_edi_send_invoice()

            if self.env.context.get('generate_pdf', True):
                self.account_move.with_context(skip_invoice_sync=True)._generate_and_send()

            return action_values
        return super()._generate_pos_order_invoice()