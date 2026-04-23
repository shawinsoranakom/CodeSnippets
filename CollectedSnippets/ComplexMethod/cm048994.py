def _l10n_es_tbai_get_vendor_bill_tax_values(self):
        self.ensure_one()
        results = defaultdict(lambda: {'base_amount': 0.0, 'tax_amount': 0.0})
        amount_total = 0.0
        for line in self.line_ids.filtered(lambda l: l.display_type in ('product', 'tax')):
            if any(t.l10n_es_type == 'ignore' for t in line.tax_ids) or line.tax_line_id.l10n_es_type == 'ignore':
                continue
            if line.tax_line_id.l10n_es_type != 'retencion':
                amount_total += line.balance
            for tax in line.tax_ids.filtered(lambda t: t.l10n_es_type not in ('recargo', 'retencion')):
                results[tax]['base_amount'] += line.balance

            if ((tax := line.tax_line_id) and tax.l10n_es_type not in ('recargo', 'retencion') and
                line.tax_repartition_line_id.factor_percent != -100.0):
                results[tax]['tax_amount'] += line.balance
        iva_values = []
        for tax in results:
            code = "C"  # Bienes Corrientes
            if tax.l10n_es_bien_inversion:
                code = "I"  # Investment Goods
            if tax.tax_scope == 'service':
                code = 'G'  # Gastos
            iva_values.append({'base': results[tax]['base_amount'],
                               'code': code,
                               'tax': results[tax]['tax_amount'],
                               'rec': tax})
        return {'iva_values': iva_values,
                'amount_total': amount_total}