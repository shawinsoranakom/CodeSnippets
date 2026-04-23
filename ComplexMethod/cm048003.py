def _l10n_es_edi_verifactu_get_record_values(self, cancellation=False):
        self.ensure_one()

        company = self.company_id
        document_type = 'cancellation' if cancellation else 'submission'
        vals = {
            'company': company,
            'record': self,
            'cancellation': cancellation,
            'errors': self._l10n_es_edi_verifactu_check(cancellation=cancellation),
            'document_vals': {
                'move_id': self.id,
                'company_id': company.id,
                'document_type': document_type,
            },
        }

        if vals['errors']:
            return vals

        documents = self.l10n_es_edi_verifactu_document_ids
        # Just checking whether the last document was rejected is enough; we do not allow to submit the same record
        # again after a cancellation (else we get the error '[3000] Registro de facturación duplicado.').
        rejected_before = documents._get_last(document_type).state == 'rejected'

        tax_applicability = self._l10n_es_edi_verifactu_get_tax_applicability()
        selected_clave_regimen = self.l10n_es_edi_verifactu_clave_regimen
        clave_regimen = selected_clave_regimen and selected_clave_regimen.split('_', 1)[0]
        substituted_move = self.l10n_es_edi_verifactu_substituted_entry_id
        reversed_move = self.reversed_entry_id

        move_type = self.move_type
        if move_type == 'out_invoice' and substituted_move:
            verifactu_move_type = 'correction_substitution'
        elif move_type == 'out_invoice':
            verifactu_move_type = 'invoice'
        elif move_type == 'out_refund' and reversed_move.l10n_es_edi_verifactu_substitution_move_ids:
            verifactu_move_type = 'reversal_for_substitution'
        else:
            # move_type == 'out_refund' and not reversed_move.l10n_es_edi_verifactu_substitution_move_ids
            verifactu_move_type = 'correction_incremental'

        vals.update({
            'rejected_before': rejected_before,
            'verifactu_state': self.l10n_es_edi_verifactu_state,
            'delivery_date': self.delivery_date,
            'description': self.invoice_origin[:500] if self.invoice_origin else None,
            'invoice_date': self.invoice_date,
            'is_simplified': self.l10n_es_is_simplified,
            'move_type': move_type,
            'verifactu_move_type': verifactu_move_type,
            'sign': -1 if move_type == 'out_refund' else 1,
            'name': self.name,
            'partner': self.commercial_partner_id,
            'refund_reason': self.l10n_es_edi_verifactu_refund_reason,
            'refunded_document': reversed_move.l10n_es_edi_verifactu_document_ids._get_last('submission'),
            'substituted_document': substituted_move.l10n_es_edi_verifactu_document_ids._get_last('submission'),
            'substituted_document_reversal_document': substituted_move.reversal_move_ids.l10n_es_edi_verifactu_document_ids._get_last('submission'),
            'documents': documents,
            'record_identifier': documents._get_last('submission')._get_record_identifier(),
            'l10n_es_applicability': tax_applicability,
            'clave_regimen': clave_regimen or None,
        })

        base_amls = self.line_ids.filtered(lambda x: x.display_type == 'product')
        base_lines = [self._prepare_product_base_line_for_taxes_computation(x) for x in base_amls]
        epd_amls = self.line_ids.filtered(lambda line: line.display_type == 'epd')
        base_lines += [self._prepare_epd_base_line_for_taxes_computation(line) for line in epd_amls]
        cash_rounding_amls = self.line_ids \
            .filtered(lambda line: line.display_type == 'rounding' and not line.tax_repartition_line_id)
        base_lines += [self._prepare_cash_rounding_base_line_for_taxes_computation(line) for line in cash_rounding_amls]
        tax_amls = self.line_ids.filtered('tax_repartition_line_id')
        tax_lines = [self._prepare_tax_line_for_taxes_computation(x) for x in tax_amls]
        vals['tax_details'] = self.env['l10n_es_edi_verifactu.document']._get_tax_details(base_lines, company, tax_lines=tax_lines)

        return vals