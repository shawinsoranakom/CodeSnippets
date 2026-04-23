def _l10n_it_edi_get_values(self, pdf_values=None):
        def grouping_function_withholding(base_line, tax_data):
            if not tax_data:
                return None
            tax = tax_data['tax']
            return {
                'tax_amount_field': -23.0 if tax.amount in (-11.5, -4.6) else tax.amount,
                'l10n_it_withholding_type': tax.l10n_it_withholding_type,
                'l10n_it_withholding_reason': tax.l10n_it_withholding_reason,
                'skip': not tax._l10n_it_filter_kind('withholding'),
            }

        def grouping_function_pension_funds(base_line, tax_data):
            if not tax_data:
                return None
            tax = tax_data['tax']
            flatten_taxes = base_line['tax_ids'].flatten_taxes_hierarchy()
            vat_tax = flatten_taxes.filtered(lambda t: t._l10n_it_filter_kind('vat') and t.amount >= 0)[:1]
            withholding_tax = flatten_taxes.filtered(lambda t: t._l10n_it_filter_kind('withholding') and t.sequence > tax.sequence)[:1]
            return {
                'tax_amount_field': -23.0 if tax.amount in (-11.5, -4.6) else tax.amount,
                'vat_tax_amount_field': -23.0 if vat_tax.amount in (-11.5, -4.6) else vat_tax.amount,
                'has_withholding': bool(withholding_tax),
                'l10n_it_pension_fund_type': tax.l10n_it_pension_fund_type,
                'l10n_it_exempt_reason': vat_tax.l10n_it_exempt_reason,
                'description': vat_tax.description,
                'skip': not tax._l10n_it_filter_kind('pension_fund') or tax.l10n_it_pension_fund_type == 'TC07',
            }

        self.ensure_one()

        # Flags
        is_self_invoice = self.l10n_it_edi_is_self_invoice
        document_type = self.l10n_it_document_type.code

        # Represent if the document is a reverse charge refund in a single variable
        reverse_charge = document_type in ['TD16', 'TD17', 'TD18', 'TD19']
        is_downpayment = document_type in ['TD02']
        reverse_charge_refund = self.move_type == 'in_refund' and reverse_charge
        convert_to_euros = self.currency_id.name != 'EUR'

        # Base lines.
        base_amls = self.line_ids.filtered(lambda x: x.display_type == 'product' or x.display_type == 'rounding')

        n7_tax = self.env['account.chart.template'].ref('00ex7', raise_if_not_found=False)
        n22_tax = self.env['account.chart.template'].ref('00ex', raise_if_not_found=False)
        base_lines = []
        for aml in base_amls:
            base_line = self._prepare_product_base_line_for_taxes_computation(aml)
            vat_tax = aml.tax_ids.flatten_taxes_hierarchy().filtered(lambda t: t._l10n_it_filter_kind('vat') and t.amount >= 0)[:1]
            is_oss = vat_tax and 'OSS' in vat_tax.invoice_repartition_line_ids.tag_ids.mapped('name')
            if is_oss and n7_tax and n22_tax:
                base_lines += self._l10n_it_edi_get_oss_line_values(aml, base_line, vat_tax, n7_tax, n22_tax)
            else:
                base_lines.append(base_line)
        tax_amls = self.line_ids.filtered('tax_repartition_line_id')
        tax_lines = [self._prepare_tax_line_for_taxes_computation(x) for x in tax_amls]

        if reverse_charge_refund:
            for base_line in base_lines:
                base_line['price_unit'] *= -1

        AccountTax = self.env['account.tax']
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)

        downpayment_lines = []
        for base_line in base_lines:
            tax_details = base_line['tax_details']
            discount = base_line['discount']
            price_unit = base_line['price_unit']
            quantity = base_line['quantity']
            price_subtotal = base_line['price_subtotal'] = tax_details['raw_total_excluded_currency']

            if discount == 100.0:
                gross_price_subtotal_before_discount = price_unit * quantity
            else:
                gross_price_subtotal_before_discount = price_subtotal / (1 - discount / 100.0)

            base_line['gross_price_subtotal'] = gross_price_subtotal_before_discount
            base_line['discount_amount_before_dispatching'] = gross_price_subtotal_before_discount - price_subtotal

            # The tax "23% Ritenuta Agenti e Rappresentanti" is not supported because it's supposed to be a tax of 23% based on
            # 50% or 20% of the base amount. It's currently implemented as a -11.5% or -4.6% tax respectively. So on 1000, it
            # gives an amount of -115(for 50%) or -46(for 20%).
            # We need to fix the base amount from 1000 to 500.0 or 200.0.
            for tax_data in tax_details['taxes_data']:
                tax = tax_data['tax']
                tax_data['_tax_amount'] = tax.amount
                if tax.amount == -11.5:
                    tax_data['_tax_amount'] = -23.0
                    tax_data['raw_base_amount'] *= 0.5
                    tax_data['raw_base_amount_currency'] *= 0.5
                elif tax.amount == -4.6:
                    tax_data['_tax_amount'] = -23.0
                    tax_data['raw_base_amount'] *= 0.2
                    tax_data['raw_base_amount_currency'] *= 0.2

            if not is_downpayment:
                # Negative lines linked to down payment should stay negative
                line = base_line['record']
                if line.price_subtotal < 0 and line._get_downpayment_lines():
                    downpayment_lines.append(base_line)

            if float_compare(quantity, 0, 2) < 0:
                # Negative quantity is refused by SDI, so we invert quantity and price_unit to keep the price_subtotal
                base_line.update({
                    'quantity': -quantity,
                    'price_unit': -price_unit,
                })

        AccountTax._round_base_lines_tax_details(base_lines, self.company_id, tax_lines=tax_lines)
        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, self._l10n_it_edi_grouping_function_base_lines)
        self._l10n_it_edi_add_base_lines_xml_values(base_lines_aggregated_values, is_downpayment)
        base_lines = sorted(base_lines, key=lambda base_line: base_line['it_values']['numero_linea'])

        # Tax lines.
        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, self._l10n_it_edi_grouping_function_tax_lines)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        tax_lines = self._l10n_it_edi_get_tax_lines_xml_values(base_lines_aggregated_values, values_per_grouping_key)

        # Total of the document.
        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, self._l10n_it_edi_grouping_function_total)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        importo_totale_documento = 0.0
        for values in values_per_grouping_key.values():
            grouping_key = values['grouping_key']
            if grouping_key is False:
                continue
            importo_totale_documento += values['base_amount']
            importo_totale_documento += values['tax_amount']

        company = self.company_id._l10n_it_get_edi_company()
        partner = self.commercial_partner_id
        sender = company
        buyer = partner if not is_self_invoice else company
        seller = company if not is_self_invoice else partner
        sender_info_values = company.partner_id._l10n_it_edi_get_values()
        buyer_info_values = (partner if not is_self_invoice else company.partner_id)._l10n_it_edi_get_values()
        seller_info_values = (company.partner_id if not is_self_invoice else partner)._l10n_it_edi_get_values()
        representative_info_values = company.l10n_it_tax_representative_partner_id._l10n_it_edi_get_values()

        if self._l10n_it_edi_is_simplified_document_type(document_type):
            formato_trasmissione = "FSM10"
        elif partner._l10n_it_edi_is_public_administration():
            formato_trasmissione = "FPA12"
        else:
            formato_trasmissione = "FPR12"

        # Reference line for finding the conversion rate used in the document
        conversion_rate = float_repr(
            abs(self.amount_total / self.amount_total_signed), precision_digits=5,
        ) if convert_to_euros and self.invoice_line_ids and not self.currency_id.is_zero(self.amount_total_signed) else None

        # Aggregated linked invoices
        linked_moves = (self._get_reconciled_invoices() | self.reversed_entry_id).filtered(lambda move: move.date <= self.date)

        # Reduce downpayment views to a single recordset
        linked_moves |= self.invoice_line_ids._get_downpayment_lines().move_id

        # Withholding tax amounts.

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function_withholding)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        withholding_values = []
        for values in values_per_grouping_key.values():
            grouping_key = values['grouping_key']
            if not grouping_key or grouping_key['skip']:
                continue

            withholding_values.append({
                'tipo_ritenuta': grouping_key['l10n_it_withholding_type'],
                'importo_ritenuta': -values['tax_amount'],
                'aliquota_ritenuta': -grouping_key['tax_amount_field'],
                'causale_pagamento': grouping_key['l10n_it_withholding_reason'],
            })

        # Pension fund.
        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function_pension_funds)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        pension_fund_values = []
        for values in values_per_grouping_key.values():
            grouping_key = values['grouping_key']
            if not grouping_key or grouping_key['skip']:
                continue

            pension_fund_values.append({
                'tipo_cassa': grouping_key['l10n_it_pension_fund_type'],
                'al_cassa': grouping_key['tax_amount_field'],
                'importo_contributo_cassa': values['tax_amount'],
                'imponibile_cassa': values['base_amount'],
                'aliquota_iva': grouping_key['vat_tax_amount_field'],
                'ritenuta': 'SI' if grouping_key['has_withholding'] else None,
                'natura': grouping_key['l10n_it_exempt_reason'],
                'riferimento_amministrazione': html2plaintext(grouping_key['description']),
            })

        # Enasarco values.
        for base_line in base_lines:
            taxes_data = base_line['tax_details']['taxes_data']
            it_values = base_line['it_values']
            other_data_list = it_values['altri_dati_gestionali_list']

            # Withholding
            if any(x for x in taxes_data if x['tax']._l10n_it_filter_kind('withholding')):
                it_values['ritenuta'] = 'SI'

            # Enasarco
            enasarco_taxes_data = [x for x in taxes_data if x['tax'].l10n_it_pension_fund_type == 'TC07']
            for enasarco_tax_data in enasarco_taxes_data:
                percentage_str = round(abs(enasarco_tax_data['tax'].amount), 1)
                other_data_list.append({
                    'tipo_dato': 'CASSA-PREV',
                    'riferimento_testo': f'TC07 - ENASARCO ({percentage_str}%)',
                    'riferimento_numero': -enasarco_tax_data['tax_amount'],
                    'riferimento_data': None,
                })

            # Pension Fund
            if not enasarco_taxes_data:
                pension_fund_taxes_data = [x for x in taxes_data if x['tax']._l10n_it_filter_kind('pension_fund')]
                for pension_fund_tax_data in pension_fund_taxes_data:
                    pension_type = pension_fund_tax_data['tax'].l10n_it_pension_fund_type
                    percentage_str = round(abs(pension_fund_tax_data['tax'].amount))
                    other_data_list.append({
                        'tipo_dato': 'AswCassPre',
                        'riferimento_testo': f'{pension_type} ({percentage_str}%)',
                        'riferimento_numero': None,
                        'riferimento_data': None,
                    })

        return {
            'record': self,
            'base_lines': base_lines,
            'tax_lines': tax_lines,
            'importo_totale_documento': importo_totale_documento,
            'company': company,
            'partner': partner,
            'sender': sender,
            'buyer': buyer,
            'seller': seller,
            'representative': company.l10n_it_tax_representative_partner_id,
            'sender_info': sender_info_values,
            'buyer_info': buyer_info_values,
            'seller_info': seller_info_values,
            'representative_info': representative_info_values,
            'origin_document_type': self.l10n_it_origin_document_type,
            'origin_document_name': self.l10n_it_origin_document_name,
            'origin_document_date': self.l10n_it_origin_document_date,
            'cig': self.l10n_it_cig,
            'cup': self.l10n_it_cup,
            'currency': self.currency_id or self.company_currency_id if not convert_to_euros else self.env.ref('base.EUR'),
            'regime_fiscale': company.l10n_it_tax_system if not is_self_invoice else 'RF18',
            'is_self_invoice': is_self_invoice,
            'partner_bank': self.partner_bank_id,
            'formato_trasmissione': formato_trasmissione,
            'document_type': document_type,
            'payment_method': self.l10n_it_payment_method,
            'linked_moves': linked_moves,
            'rc_refund': reverse_charge_refund,
            'conversion_rate': conversion_rate,
            'balance_multiplicator': -1 if self.is_inbound() else 1,
            'abs': abs,
            'pdf_name': pdf_values['name'] if pdf_values else False,
            'pdf': b64encode(pdf_values['raw']).decode() if pdf_values else False,
            'withholding_values': withholding_values,
            'pension_fund_values': pension_fund_values,
        }