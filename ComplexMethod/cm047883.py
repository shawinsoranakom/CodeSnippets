def _process_saved_order(self, draft):
        self.ensure_one()
        if self.l10n_es_edi_verifactu_required:
            if not self.to_invoice and self.amount_total > self.company_id.l10n_es_simplified_invoice_limit:
                raise UserError(_("The order needs to be invoiced since its total amount is above %s€.",
                                  self.company_id.l10n_es_simplified_invoice_limit))
            refunded_order = self.refunded_order_id
            if refunded_order:
                if not self.l10n_es_edi_verifactu_refund_reason:
                    raise UserError(_("You have to specify a refund reason."))
                simplified_partner = self.env.ref('l10n_es.partner_simplified', raise_if_not_found=False)
                partner_specified = self.partner_id and self.partner_id != simplified_partner
                if not partner_specified and self.l10n_es_edi_verifactu_refund_reason != 'R5':
                    raise UserError(_("A partner has to be specified for the selected Veri*Factu Refund Reason."))

        return super()._process_saved_order(draft)