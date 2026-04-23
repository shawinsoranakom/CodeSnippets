def action_export(self):
        self.ensure_one()
        domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('country_code', '=', 'HU'),
        ]
        if self.selection_mode == 'date':
            if self.date_from:
                domain.append(('date', '>=', self.date_from))
            if self.date_to:
                domain.append(('date', '<=', self.date_to))
        else:
            if self.name_from:
                domain.append(('name', '>=', self.name_from))
            if self.name_to:
                domain.append(('name', '<=', self.name_to))

        invoices = self.env['account.move'].search(domain)
        if not invoices:
            raise UserError(_('No invoice to export!'))

        with io.BytesIO() as buf:
            with zipfile.ZipFile(buf, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=False) as zf:
                # To correctly generate the XML for invoices created before l10n_hu_edi was installed,
                # we need to temporarily set the chain index and line numbers, so we do this in a savepoint.
                with contextlib.closing(self.env.cr.savepoint()):
                    for invoice in invoices.sorted(lambda i: i.create_date):
                        if invoice.l10n_hu_edi_state:
                            # Case 1: An XML was already generated for this invoice.
                            invoice_xml = base64.b64decode(invoice.l10n_hu_edi_attachment)
                        else:
                            # Case 2: No XML was generated for this invoice.
                            if not invoice.l10n_hu_invoice_chain_index:
                                invoice._l10n_hu_edi_set_chain_index()
                            invoice_xml = invoice._l10n_hu_edi_generate_xml()

                        filename = f'{invoice.name.replace("/", "_")}.xml'
                        zf.writestr(filename, invoice_xml)
            self.export_file = base64.b64encode(buf.getvalue())

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }