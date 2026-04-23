def _compute_qr_code_str(self):
        """ Override to update QR code generation in accordance with ZATCA Phase 2"""
        phase_one_moves = self.env['account.move']
        for move in self:
            zatca_document = move.edi_document_ids.filtered(lambda d: d.edi_format_id.code == 'sa_zatca')
            if move.country_code == 'SA' and move.move_type in ('out_invoice', 'out_refund') and zatca_document and move.state != 'draft':
                qr_code_str = ''
                if move._l10n_sa_is_simplified():
                    x509_cert = move.journal_id.l10n_sa_production_csid_certificate_id
                    xml_content = self.env.ref('l10n_sa_edi.edi_sa_zatca')._l10n_sa_generate_zatca_template(move)
                    qr_code_str = move._l10n_sa_get_qr_code(move.company_id, xml_content, x509_cert,
                                                            move.l10n_sa_invoice_signature, True)
                    qr_code_str = b64encode(qr_code_str).decode()
                elif zatca_document.state == 'sent' and zatca_document.attachment_id.datas:
                    document_xml = zatca_document.attachment_id.with_context(bin_size=False).datas.decode()
                    root = etree.fromstring(b64decode(document_xml))
                    qr_node = root.xpath('//*[local-name()="ID"][text()="QR"]/following-sibling::*/*')[0]
                    qr_code_str = qr_node.text
                move.l10n_sa_qr_code_str = qr_code_str
            else:
                # In the case where the Invoice is not a ZATCA invoice, or is Phase 1, or is not confirmed,
                # we call super to trigger the initial QR code generation for Phase 1
                phase_one_moves |= move
        super(AccountMove, phase_one_moves)._compute_qr_code_str()