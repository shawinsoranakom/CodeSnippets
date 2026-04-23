def _l10n_es_edi_get_invoices_tax_details_info(self, invoice, filter_invl_to_apply=None):

        def grouping_key_generator(base_line, tax_data):
            tax = tax_data['tax']
            return {
                'applied_tax_amount': tax.amount,
                'l10n_es_type': tax.l10n_es_type,
                'l10n_es_exempt_reason': tax.l10n_es_exempt_reason if tax.l10n_es_type == 'exento' else False,
                'l10n_es_bien_inversion': tax.l10n_es_bien_inversion,
            }

        def filter_to_apply(base_line, tax_data):
            # For intra-community, we do not take into account the negative repartition line
            return (
                not tax_data['is_reverse_charge']
                and tax_data['tax'].amount != -100.0
                and tax_data['tax'].l10n_es_type != 'ignore'
            )

        def full_filter_invl_to_apply(invoice_line):
            if all(t == 'ignore' for t in invoice_line.tax_ids.flatten_taxes_hierarchy().mapped('l10n_es_type')):
                return False
            return filter_invl_to_apply(invoice_line) if filter_invl_to_apply else True

        tax_details = invoice._prepare_edi_tax_details(
            grouping_key_generator=grouping_key_generator,
            filter_invl_to_apply=full_filter_invl_to_apply,
            filter_to_apply=filter_to_apply,
        )
        sign = -1 if invoice.move_type in ('out_refund', 'in_refund') else 1

        tax_details_info = defaultdict(dict)

        # Detect for which is the main tax for 'recargo'. Since only a single combination tax + recargo is allowed
        # on the same invoice, this can be deduced globally.

        # Mapping between main tax and recargo tax details
        # structure: {("l10n_es_type" of the main tax, amount of the main tax): {'tax_amount': float, 'applied_tax_amount': float}}
        # dict of keys: tuple ("l10n_es_type" of the main tax, amount of the main tax)
        #       values: dict of float
        recargo_tax_details = defaultdict(lambda: defaultdict(float))
        for base_line in tax_details['base_lines']:
            line = base_line['record']
            taxes = line.tax_ids.flatten_taxes_hierarchy()
            recargo_tax = taxes.filtered(lambda t: t.l10n_es_type == 'recargo')[:1]
            if recargo_tax and taxes:
                recargo_main_tax = taxes.filtered(lambda x: x.l10n_es_type in ('sujeto', 'sujeto_isp'))[:1]
                aggregated_values = tax_details['tax_details_per_record'][line]
                recargo_values = next(iter(
                    values
                    for values in aggregated_values['tax_details'].values()
                    if (
                        values['grouping_key']
                        and values['grouping_key']['l10n_es_type'] == recargo_tax.l10n_es_type
                        and values['grouping_key']['applied_tax_amount'] == recargo_tax.amount
                    )
                ))
                recargo_tax_details[recargo_main_tax.l10n_es_type, recargo_main_tax.amount]['tax_amount'] += recargo_values['tax_amount']
                recargo_tax_details[recargo_main_tax.l10n_es_type, recargo_main_tax.amount]['applied_tax_amount'] = recargo_values['applied_tax_amount']

        tax_amount_deductible = 0.0
        tax_amount_retention = 0.0
        base_amount_not_subject = 0.0
        base_amount_not_subject_loc = 0.0
        tax_subject_info_list = []
        tax_subject_isp_info_list = []
        for tax_values in tax_details['tax_details'].values():
            recargo = recargo_tax_details.get((tax_values['l10n_es_type'], tax_values['applied_tax_amount']))
            if invoice.is_sale_document():
                # Customer invoices

                if tax_values['l10n_es_type'] in ('sujeto', 'sujeto_isp'):
                    tax_amount_deductible += tax_values['tax_amount']

                    base_amount = sign * tax_values['base_amount']
                    tax_info = {
                        'TipoImpositivo': tax_values['applied_tax_amount'],
                        'BaseImponible': float_round(base_amount, 2),
                        'CuotaRepercutida': float_round(math.copysign(tax_values['tax_amount'], base_amount), 2),
                    }

                    if recargo:
                        tax_info['CuotaRecargoEquivalencia'] = float_round(sign * recargo['tax_amount'], 2)
                        tax_info['TipoRecargoEquivalencia'] = recargo['applied_tax_amount']

                    if tax_values['l10n_es_type'] == 'sujeto':
                        tax_subject_info_list.append(tax_info)
                    else:
                        tax_subject_isp_info_list.append(tax_info)

                elif tax_values['l10n_es_type'] == 'exento':
                    tax_details_info['Sujeta'].setdefault('Exenta', {'DetalleExenta': []})
                    tax_details_info['Sujeta']['Exenta']['DetalleExenta'].append({
                        'BaseImponible': float_round(sign * tax_values['base_amount'], 2),
                        'CausaExencion': tax_values['l10n_es_exempt_reason'],
                    })
                elif tax_values['l10n_es_type'] == 'retencion':
                    tax_amount_retention += tax_values['tax_amount']
                elif tax_values['l10n_es_type'] == 'no_sujeto':
                    base_amount_not_subject += tax_values['base_amount']
                elif tax_values['l10n_es_type'] == 'no_sujeto_loc':
                    base_amount_not_subject_loc += tax_values['base_amount']
                elif tax_values['l10n_es_type'] == 'ignore':
                    continue

            else:
                # Vendor bills
                if tax_values['l10n_es_type'] in ('sujeto', 'sujeto_isp', 'no_sujeto', 'no_sujeto_loc', 'dua', 'sujeto_agricultura'):
                    tax_amount_deductible += tax_values['tax_amount']
                elif tax_values['l10n_es_type'] == 'retencion':
                    tax_amount_retention += tax_values['tax_amount']
                elif tax_values['l10n_es_type'] == 'no_sujeto':
                    base_amount_not_subject += tax_values['base_amount']
                elif tax_values['l10n_es_type'] == 'no_sujeto_loc':
                    base_amount_not_subject_loc += tax_values['base_amount']
                elif tax_values['l10n_es_type'] == 'ignore':
                    continue

                if tax_values['l10n_es_type'] not in ['retencion', 'recargo']: # = in sujeto/sujeto_isp/no_deducible
                    base_amount = sign * tax_values['base_amount']
                    tax_details_info.setdefault('DetalleIVA', [])
                    tax_info = {
                        'BaseImponible': float_round(base_amount, 2),
                    }
                    if tax_values['l10n_es_type'] == 'sujeto_agricultura':
                        tax_info.update({
                            'PorcentCompensacionREAGYP': tax_values['applied_tax_amount'],
                            'ImporteCompensacionREAGYP': round(math.copysign(tax_values['tax_amount'], base_amount), 2),
                        })
                    elif tax_values['applied_tax_amount'] > 0.0:
                        tax_info.update({
                            'TipoImpositivo': tax_values['applied_tax_amount'],
                            'CuotaSoportada': float_round(math.copysign(tax_values['tax_amount'], base_amount), 2),
                        })
                    if tax_values['l10n_es_bien_inversion']:
                        tax_info['BienInversion'] = 'S'
                    if recargo:
                        tax_info['CuotaRecargoEquivalencia'] = float_round(sign * recargo['tax_amount'], 2)
                        tax_info['TipoRecargoEquivalencia'] = recargo['applied_tax_amount']
                    tax_details_info['DetalleIVA'].append(tax_info)

        if tax_subject_isp_info_list and not tax_subject_info_list:  # Only for sale_invoices
            tax_details_info['Sujeta']['NoExenta'] = {'TipoNoExenta': 'S2'}
        elif not tax_subject_isp_info_list and tax_subject_info_list:
            tax_details_info['Sujeta']['NoExenta'] = {'TipoNoExenta': 'S1'}
        elif tax_subject_isp_info_list and tax_subject_info_list:
            tax_details_info['Sujeta']['NoExenta'] = {'TipoNoExenta': 'S3'}

        if tax_subject_info_list:
            tax_details_info['Sujeta']['NoExenta'].setdefault('DesgloseIVA', {})
            tax_details_info['Sujeta']['NoExenta']['DesgloseIVA'].setdefault('DetalleIVA', [])
            tax_details_info['Sujeta']['NoExenta']['DesgloseIVA']['DetalleIVA'] += tax_subject_info_list
        if tax_subject_isp_info_list:
            tax_details_info['Sujeta']['NoExenta'].setdefault('DesgloseIVA', {})
            tax_details_info['Sujeta']['NoExenta']['DesgloseIVA'].setdefault('DetalleIVA', [])
            tax_details_info['Sujeta']['NoExenta']['DesgloseIVA']['DetalleIVA'] += tax_subject_isp_info_list

        if not invoice.company_id.currency_id.is_zero(base_amount_not_subject) and invoice.is_sale_document():
            tax_details_info['NoSujeta']['ImportePorArticulos7_14_Otros'] = float_round(sign * base_amount_not_subject, 2)
        if not invoice.company_id.currency_id.is_zero(base_amount_not_subject_loc) and invoice.is_sale_document():
            tax_details_info['NoSujeta']['ImporteTAIReglasLocalizacion'] = float_round(sign * base_amount_not_subject_loc, 2)
        if not tax_details_info and invoice.is_sale_document():
            if any(t['l10n_es_type'] == 'no_sujeto' for t in tax_details['tax_details'].values()):
                tax_details_info['NoSujeta']['ImportePorArticulos7_14_Otros'] = 0
            if any(t['l10n_es_type'] == 'no_sujeto_loc' for t in tax_details['tax_details'].values()):
                tax_details_info['NoSujeta']['ImporteTAIReglasLocalizacion'] = 0

        return {
            'tax_details_info': tax_details_info,
            'tax_details': tax_details,
            'tax_amount_deductible': tax_amount_deductible,
            'tax_amount_retention': tax_amount_retention,
            'base_amount_not_subject': base_amount_not_subject,
            'S1_list': tax_subject_info_list, #TBAI has separate sections for S1 and S2
            'S2_list': tax_subject_isp_info_list, #TBAI has separate sections for S1 and S2
        }