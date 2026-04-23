def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        if self.journal_id.company_id.account_fiscal_country_id != self.env.ref('base.cl') or not \
                self.l10n_latam_use_documents:
            return super()._get_l10n_latam_documents_domain()
        if self.journal_id.type == 'sale':
            domain = [('country_id.code', '=', 'CL')]
            if self.move_type in ['in_invoice', 'out_invoice']:
                domain += [('internal_type', 'in', ['invoice', 'debit_note', 'invoice_in'])]
            elif self.move_type in ['in_refund', 'out_refund']:
                domain += [('internal_type', '=', 'credit_note')]
            if self.company_id.partner_id.l10n_cl_sii_taxpayer_type == '1':
                domain += [('code', '!=', '71')]  # Companies with VAT Affected doesn't have "Boleta de honorarios Electrónica"
            return domain
        if self.move_type == 'in_refund':
            internal_types_domain = ('internal_type', '=', 'credit_note')
        else:
            internal_types_domain = ('internal_type', 'in', ['invoice', 'debit_note', 'invoice_in'])
        domain = [
            ('country_id.code', '=', 'CL'),
            internal_types_domain,
        ]
        if self.partner_id.l10n_cl_sii_taxpayer_type == '1' and self.partner_id_vat != '60805000-0':
            domain += [('code', 'not in', ['39', '70', '71', '914', '911'])]
        elif self.partner_id.l10n_cl_sii_taxpayer_type == '1' and self.partner_id_vat == '60805000-0':
            domain += [('code', 'not in', ['39', '70', '71'])]
        elif self.partner_id.l10n_cl_sii_taxpayer_type == '2':
            domain += [('code', '=', '71')]
        elif self.partner_id.l10n_cl_sii_taxpayer_type == '3':
            domain += [('code', 'in', ['35', '38', '39', '41', '56', '61'])]
        elif self.partner_id.country_id.code != 'CL' or self.partner_id.l10n_cl_sii_taxpayer_type == '4':
            domain += [('code', '=', '46')]
        else:
            domain += [('code', 'in', [])]
        return domain