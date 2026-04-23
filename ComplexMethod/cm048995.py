def _check_can_post(self, values):
        # Ensure a certificate is available.
        if not self.company_id.l10n_es_tbai_certificate_id:
            return _("Please configure the certificate for TicketBAI.")

        # Ensure a tax agency is available.
        if not self.company_id.l10n_es_tbai_tax_agency:
            return _("Please specify a tax agency on your company for TicketBAI.")

        # Ensure a vat is available.
        if not self.company_id.vat:
            return _("Please configure the Tax ID on your company for TicketBAI.")

        if self.company_id.l10n_es_tbai_tax_agency == 'bizkaia' and self.company_id._l10n_es_freelancer() and not self.env['ir.config_parameter'].sudo().get_param('l10n_es_edi_tbai.epigrafe', False):
            return _("In order to use Ticketbai Batuz for freelancers, you will need to configure the "
                        "Epigrafe or Main Activity.  In this version, you need to go in debug mode to "
                        "Settings > Technical > System Parameters and set the parameter 'l10n_es_edi_tbai.epigrafe'"
                        "to your epigrafe number. You can find them in %s",
                        "https://www.batuz.eus/fitxategiak/batuz/lroe/batuz_lroe_lista_epigrafes_v1_0_3.xlsx")

        if values['is_sale'] and not self.is_cancel:
            if any(not base_line['tax_ids'] for base_line in values['base_lines']):
                return self.env._("There should be at least one tax set on each line in order to send to TicketBAI.")

            # Chain integrity check: chain head must have been REALLY posted
            chain_head_doc = self.company_id._get_l10n_es_tbai_last_chained_document()
            if chain_head_doc and chain_head_doc != self and chain_head_doc.state != 'accepted':
                return _("TicketBAI: Cannot post invoice while chain head (%s) has not been posted", chain_head_doc.name)

            # Tax configuration check: In case of foreign customer we need the tax scope to be set
            if values['partner'] and values['partner']._l10n_es_is_foreign() and values['taxes'].filtered(lambda t: not t.tax_scope):
                return _(
                    "In case of a foreign customer, you need to configure the tax scope on taxes:\n%s",
                    "\n".join(values['taxes'].mapped('name'))
                )
            if values['is_refund']:
                refunded_doc = values['refunded_doc']
                refund_reason = values['refund_reason']
                refunded_doc_invoice_date = values['refunded_doc_invoice_date']
                is_simplified = values['is_simplified']

                if not refunded_doc or refunded_doc.state == 'to_send':
                    invoice_sent_before_original = True
                    if not refunded_doc and refunded_doc_invoice_date:
                        domain = [('date', '<', refunded_doc_invoice_date),
                                  ('company_id', '=', self.company_id.id),
                                  ('chain_index', '!=', 0)]
                        invoice_sent_before_original = self.search(domain, order="date", limit=1)
                    if invoice_sent_before_original:  # No error if the original invoice was imported from a previous system
                        return _("TicketBAI: Cannot post a reversal document while the source document has not been posted")
                if not refund_reason:
                    return _('Refund reason must be specified (TicketBAI)')
                if is_simplified and refund_reason != 'R5':
                    return _('Refund reason must be R5 for simplified invoices (TicketBAI)')
                if not is_simplified and refund_reason == 'R5':
                    return _('Refund reason cannot be R5 for non-simplified invoices (TicketBAI)')