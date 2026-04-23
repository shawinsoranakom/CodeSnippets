def download_efaktur(self):
        """OVERRIDE l10n_id_efaktur

        Change the flow of efaktur downloading. Collects data needed for efaktur and generate the
        xml file.
        """
        # Pre-download checks

        # Should prevent users from generating e-Faktur document on invoices across multi-company.
        # Allowing it will cause issues on the invoice/eFaktur document record rule
        if len(self.company_id) > 1:
            raise UserError(_("You are not allowed to generate e-Faktur document from invoices coming from different companies"))

        err_messages = []

        if not self.company_id.vat:
            err_messages.append(_("Your company's VAT hasn't been configured yet"))

        # check for every customer
        for partner in self.partner_id:
            comm = partner.commercial_partner_id
            if not comm.l10n_id_pkp:
                err_messages.append(_("Customer %s is not taxable, tick ID PKP if necessary", comm.name))
            if comm.l10n_id_buyer_document_type != 'TIN' and not comm.l10n_id_buyer_document_number:
                err_messages.append(_("Document number for customer %s hasn't been filled in", comm.name))
            if not comm.vat:
                err_messages.append(_("NPWP for customer %s hasn't been filled in yet", comm.name))
            if not comm.country_id:
                err_messages.append(_("No country is set for customer %s", comm.name))

        # check for every invoice
        for record in self:
            if record.state == 'draft':
                err_messages.append(_('Invoice %s is in draft state', record.name))
            if not record.country_code == 'ID':
                err_messages.append(_("Invoice %s is not under Indonesian company", record.name))
            if not record.move_type == 'out_invoice':
                err_messages.append(_("Entry %s is not an invoice", record.name))
            if not record.line_ids.tax_ids:
                err_messages.append(_("Invoice %s does not contain any taxes", record.name))
            if record.l10n_id_kode_transaksi == "07":
                if not (record.l10n_id_coretax_add_info_07 and record.l10n_id_coretax_facility_info_07):
                    err_messages.append(_("Invoice %s doesn't contain the Additional info and Facility Stamp yet (Kode 07)", record.name))
            if record.l10n_id_kode_transaksi == "08":
                if not (record.l10n_id_coretax_add_info_08 and record.l10n_id_coretax_facility_info_08):
                    err_messages.append(_("Invoice %s doesn't contain the Additional info and Facility Stamp yet (Kode 08)", record.name))

        # Check tax groups
        err_messages.extend(self._validate_tax_groups())

        if err_messages:
            err_messages = [_('Unable to download E-faktur for the following reason(s):')] + err_messages
            raise ValidationError('\n - '.join(err_messages))

        # All invoices in self have no documents; we can create a new one for them.
        # Or all invoices in self have a document, but it's the same one. Special use case but we allow downloading it.
        if not self.l10n_id_coretax_document:
            self.l10n_id_coretax_document = self.env['l10n_id_efaktur_coretax.document'].create({
                'invoice_ids': self.ids,
                'company_id': self.company_id.id,
            })
            self.l10n_id_coretax_document._generate_xml()

        # If there is more than one document, or all invoices for a document were not selected, the resulting file could cause mistakes;
        # They could get a file with additional invoices for example. In this case, we redirect them to the document view to make it clearer.
        elif len(self.l10n_id_coretax_document) > 1 or set(self.l10n_id_coretax_document.invoice_ids.ids) != set(self.ids):
            action_error = {
                'name': _('Document Mismatch'),
                'view_mode': 'list',
                'res_model': 'l10n_id_efaktur_coretax.document',
                'type': 'ir.actions.act_window',
                'views': [[False, 'list'], [False, 'form']],
                'domain': [('id', 'in', self.l10n_id_coretax_document.ids)],
            }
            msg = _("The selected invoices are partially part of one or more e-faktur documents.\n"
                    "Please download them from the e-faktur documents directly.")
            raise RedirectWarning(msg, action_error, _("Display Related Documents"))

        return self.download_xml()