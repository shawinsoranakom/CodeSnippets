def _l10n_cl_get_amounts(self):
        """
        This method is used to calculate the amount and taxes required in the Chilean localization electronic documents.
        """
        self.ensure_one()
        global_discounts = self.invoice_line_ids.filtered(lambda x: x.price_subtotal < 0)
        export = self.l10n_latam_document_type_id._is_doc_type_export()
        main_currency = self.company_id.currency_id if not export else self.currency_id
        key_main_currency = 'amount_currency' if export else 'balance'
        sign_main_currency = -1 if self.move_type == 'out_invoice' else 1
        currency_round_main_currency = self.currency_id if export else self.company_id.currency_id
        currency_round_other_currency = self.company_id.currency_id if export else self.currency_id
        total_amount_main_currency = currency_round_main_currency.round(self.amount_total) if export \
            else (currency_round_main_currency.round(abs(self.amount_total_signed)))
        other_currency = self.currency_id != self.company_id.currency_id
        values = {
            'main_currency': main_currency,
            'vat_amount': 0,
            'subtotal_amount_taxable': 0,
            'subtotal_amount_exempt': 0, 'total_amount': total_amount_main_currency,
            'main_currency_round': currency_round_main_currency.decimal_places,
            'main_currency_name': self._l10n_cl_normalize_currency_name(
                currency_round_main_currency.name) if export else False
        }
        vat_percent = 0

        if other_currency:
            key_other_currency = 'balance' if export else 'amount_currency'
            values['second_currency'] = {
                'subtotal_amount_taxable': 0,
                'subtotal_amount_exempt': 0,
                'vat_amount': 0,
                'total_amount': currency_round_other_currency.round(abs(self.amount_total_signed))
                    if export else currency_round_other_currency.round(self.amount_total),
                'round_currency': currency_round_other_currency.decimal_places,
                'name': self._l10n_cl_normalize_currency_name(currency_round_other_currency.name),
                'rate': round(abs(self.amount_total_signed) / self.amount_total, 4) if self.amount_total else 1,
            }
        for line in self.line_ids:
            if line.tax_line_id and line.tax_line_id.l10n_cl_sii_code == 14:
                values['vat_amount'] += line[key_main_currency] * sign_main_currency
                if other_currency:
                    values['second_currency']['vat_amount'] += line[key_other_currency] * sign_main_currency
                vat_percent = max(vat_percent, line.tax_line_id.amount)
            if line.display_type == 'product':
                if line.tax_ids.filtered(lambda x: x.l10n_cl_sii_code == 14):
                    values['subtotal_amount_taxable'] += line[key_main_currency] * sign_main_currency
                    if other_currency:
                        values['second_currency']['subtotal_amount_taxable'] += line[key_other_currency] * sign_main_currency
                elif not line.tax_ids:
                    values['subtotal_amount_exempt'] += line[key_main_currency] * sign_main_currency
                    if other_currency:
                        values['second_currency']['subtotal_amount_exempt'] += line[key_other_currency] * sign_main_currency
        values['global_discounts'] = []
        for gd in global_discounts:
            main_value = currency_round_main_currency.round(abs(gd.price_subtotal)) if \
                (not other_currency and not export) or (other_currency and export) else \
                currency_round_main_currency.round(abs(gd.balance))
            second_value = currency_round_other_currency.round(abs(gd.balance)) if other_currency and export else \
                currency_round_other_currency.round(abs(gd.price_subtotal))
            values['global_discounts'].append(
                {
                    'name': gd.name,
                    'global_discount_main_value': main_value,
                    'global_discount_second_value': second_value if second_value != main_value else False,
                    'tax_ids': gd.tax_ids,
                }
            )
        values['vat_percent'] = '%.2f' % vat_percent if vat_percent > 0 else False
        return values