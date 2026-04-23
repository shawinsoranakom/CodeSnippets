def _generate_pos_order_invoice(self):
        # Extend 'point_of_sale'
        res = super()._generate_pos_order_invoice()
        if not self.config_id.l10n_es_edi_verifactu_required:
            return res

        for order in self:
            new_documents = False

            waiting_documents = order.l10n_es_edi_verifactu_document_ids._filter_waiting()
            if waiting_documents:
                raise UserError(_("The order can not be invoiced. It is waiting to send a Veri*Factu record to the AEAT already."))

            # Cancel the order
            if order.l10n_es_edi_verifactu_state in ('accepted', 'registered_with_errors'):
                order._l10n_es_edi_verifactu_create_documents(cancellation=True)
                new_documents = True

            # Register the invoice instead. The call to `super()` may already have sent it
            invoice = order.account_move
            if invoice.l10n_es_edi_verifactu_required and invoice and not invoice.l10n_es_edi_verifactu_document_ids:
                invoice._l10n_es_edi_verifactu_create_documents()
                new_documents = True

            if new_documents:
                self.env['l10n_es_edi_verifactu.document'].trigger_next_batch()

        return res