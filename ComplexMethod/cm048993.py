def _l10n_es_tbai_get_invoice_values(self, cancel=False):
        self.ensure_one()
        base_amls = self.line_ids.filtered(lambda x: x.display_type == 'product')
        base_lines = [self._prepare_product_base_line_for_taxes_computation(x) for x in base_amls]
        for base_line in base_lines:
            base_line['name'] = base_line['record'].name
        tax_amls = self.line_ids.filtered('tax_repartition_line_id')
        tax_lines = [self._prepare_tax_line_for_taxes_computation(x) for x in tax_amls]
        self.env['l10n_es_edi_tbai.document']._add_base_lines_tax_amounts(base_lines, self.company_id, tax_lines=tax_lines)
        for base_line in base_lines:
            sign = base_line['is_refund'] and -1 or 1
            base_line['gross_price_unit'] = sign * base_line['gross_price_unit']
            base_line['discount_amount'] = sign * base_line['discount_amount']
            base_line['price_total'] = sign * base_line['price_total']
        taxes = self.invoice_line_ids.tax_ids.flatten_taxes_hierarchy()
        is_oss = any(tax._l10n_es_get_regime_code() == '17' for tax in taxes)

        return {
            **self._l10n_es_tbai_get_credit_note_values(),
            'origin': self.invoice_origin and self.invoice_origin[:250] or 'manual',
            'taxes': taxes,
            'rate':  abs(self.amount_total / self.amount_total_signed) if self.amount_total else 1,
            'base_lines': base_lines,
            'nosujeto_causa': 'IE' if is_oss else 'RL',
            **({'post_doc': self.l10n_es_tbai_post_document_id} if cancel else {}),
        }