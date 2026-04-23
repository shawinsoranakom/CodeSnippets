def _process_saved_order(self, draft):
        if not self.l10n_es_tbai_is_required:
            return super()._process_saved_order(draft)

        self.ensure_one()

        if not self.to_invoice and self.amount_total > self.company_id.l10n_es_simplified_invoice_limit:
            raise UserError(self.env._("Please create an invoice for an amount over %s.", self.company_id.l10n_es_simplified_invoice_limit))

        if self.refunded_order_id:
            if self.to_invoice and not self.refunded_order_id.account_move:
                raise UserError(self.env._("You cannot invoice a refund whose linked order hasn't been invoiced."))
            if not self.to_invoice and self.refunded_order_id.account_move:
                raise UserError(self.env._("Please invoice the refund as the linked order has been invoiced."))

        return super()._process_saved_order(draft)