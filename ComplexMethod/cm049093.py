def _l10n_pl_edi_get_xml_values(self):
        """
        Prepares a dictionary of values to be passed to the QWeb template.
        """
        self.ensure_one()

        def get_vat_country(vat):
            if not vat or vat[:2].isdecimal():
                return False
            return vat[:2].upper()

        def get_address(partner):
            return re.sub(r'\n+', r' ', partner._display_address(True))

        def get_tags(code):
            return self.env['account.account.tag']._get_tax_tags(code, self.env.ref('base.pl').id)

        def get_tag_names(line):
            return line.tax_tag_ids.with_context(lang='en_US').mapped(lambda x: re.sub(r'^[+-]', r'', x.name or ''))

        def get_amounts_from_tag(tax_tag_string):
            lines = self.line_ids.filtered(lambda line: line.tax_tag_ids & get_tags(tax_tag_string))
            if 'OSS' in tax_tag_string:
                lines = lines.filtered(lambda line: line.tax_ids if 'Base' in tax_tag_string else not line.tax_ids)
            return -sum(lines.mapped('amount_currency'))

        def get_amounts_from_tag_in_PLN_currency(tax_group_id):
            conversion_line = self.invoice_line_ids.sorted(lambda line: abs(line.balance), reverse=True)[0] if self.invoice_line_ids else None
            conversion_rate = abs(conversion_line.balance / conversion_line.amount_currency) if self.currency_id != self.env.ref('base.PLN') and conversion_line else 1
            return get_amounts_from_tag(tax_group_id) * conversion_rate

        def compute_p_12(tag_names):
            """
                Determines the KSeF tax rate code (P_12) based on the line's tax.
                Prioritizes tax amount for standard rates, and Tags/Names for special 0% cases.
                Mapping was determined by looking at the Tax Report lines.
            """
            # "0 WDT": Intra-Community supply of goods (K_21)
            if 'K_21' in tag_names:
                return "0 WDT"
            # "0 EX": Export of goods in case of 0% rate for export of goods (K_22)
            if 'K_22' in tag_names:
                return "0 EX"
            # "oo": Supply of goods, taxable person acquiring (K_31)
            if 'K_31' in tag_names:
                return "oo"
            # Services included in art. 100.1.4 (K_12)
            if 'K_12' in tag_names:
                return "np II"
            # Supply of goods/services, out of the country (K_11, OSS)
            if 'K_11' in tag_names or any('OSS' in tag for tag in tag_names):
                return "np I"
            # "zw": Supply of goods/services, domestic, exempt (K_10) - must fill P_19
            if 'K_10' in tag_names:
                return "zw"
            # "0 KR": Supply of goods/services, domestic, 0% (K_13)
            if 'K_13' in tag_names:
                return "0 KR"
            # "23": Supply of goods/services, domestic, 23% (K_19)
            if 'K_19' in tag_names:
                return "23"
            # "8": Supply of goods/services, domestic, 8% (K_17)
            if 'K_17' in tag_names:
                return "8"
            # "5": Supply of goods/services, domestic, 5% (K_15)
            if 'K_15' in tag_names:
                return "5"
            # No tax? It's exempt
            return "zw"

        ksef_type = self._l10n_pl_edi_get_ksef_invoice_type()
        invoice_lines_vals = []
        sign = -1 if 'KOR' in ksef_type else 1

        invoice_lines_tag_names = [
            {tag_name for tag_name in get_tag_names(line) if tag_name}
            for line in self.invoice_line_ids
        ]
        invoice_tag_names = set().union(*invoice_lines_tag_names)

        invoice_lines_vals = [
            {
                'NrWierszaFa': index + 1,
                'UU_ID': f"odoo-line-{line.id}",
                'P_7': line.name,
                'P_8A': line.product_uom_id.name or 'szt.',
                'P_8B': line.quantity * sign,
                'P_9A': float_repr(line.price_unit, 2),
                'P_11': float_repr(line.price_subtotal * sign, 2),
                'P_12': compute_p_12(tag_names),
            }
            for index, line in enumerate(self.invoice_line_ids)
            if (tag_names := invoice_lines_tag_names[index])
        ]

        tax_summary_vals = {}

        for group in self.tax_totals.get('groups_by_subtotal', {}).values():
            tax_rate_str = str(int((group['tax_group_amount_type'] == 'percent' and group['tax_group_amount']) or 0))
            tax_summary_vals[tax_rate_str] = {
                'net': float_repr(group['tax_group_base_amount'], 2),
                'tax': float_repr(group['tax_group_amount'], 2),
            }

        correction_info = {}
        if 'KOR' in ksef_type:
            origin = self.reversed_entry_id
            origin_ksef_id = origin.l10n_pl_edi_ref if origin else False

            correction_info = {
                'PrzyczynaKorekty': self.ref or 'Korekta',
                'TypKorekty': '1',
                'NrFaKorygowanej': origin.name if origin else 'BRAK',
                'DataWystFaKorygowanej': origin.invoice_date if origin else self.invoice_date,
                'NrKSeF': origin_ksef_id,
                'NrKSeFN': '1' if not origin_ksef_id else False,
            }

        return {
            'invoice': self,
            'DataWytworzeniaFa': fields.Datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'seller': self.company_id,
            'seller_address': get_address(self.company_id.partner_id),
            'buyer': self.commercial_partner_id,
            'buyer_address': get_address(self.commercial_partner_id),
            'invoice_lines': invoice_lines_vals,
            'tax_summary_vals': tax_summary_vals,
            'float_repr': float_repr,
            'float_is_zero': float_is_zero,
            'get_vat_country': get_vat_country,
            'get_vat_number': compact,
            'get_amounts_from_tag': get_amounts_from_tag,
            'get_amounts_from_tag_in_PLN_currency': get_amounts_from_tag_in_PLN_currency,
            'invoice_type': ksef_type,
            'related_invoices': self._l10n_pl_edi_get_related_invoices(),
            'correction_info': correction_info,
            'special_transactions': {'OSS_Base', 'OSS_Tax', 'Triangular Sale'} & invoice_tag_names,
            'triangular_transaction': '1' if 'Triangular Sale' in invoice_tag_names else '2',
        }