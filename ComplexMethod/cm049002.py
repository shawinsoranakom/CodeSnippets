def _build_tax_details_info(self, values_list):
        sujeta_no_sujeta = {}
        sujeto = []
        sujeto_isp = []
        encountered_l10n_es_type = set()
        for values in values_list:
            grouping_key = values['grouping_key']
            if not grouping_key:
                continue

            l10n_es_type = grouping_key['l10n_es_type']
            sign = grouping_key['is_refund'] and -1 or 1
            encountered_l10n_es_type.add(l10n_es_type)
            if l10n_es_type in ('sujeto', 'sujeto_isp'):
                tax_info = {
                    'TipoImpositivo': grouping_key['applied_tax_amount'],
                    'BaseImponible': sign * float_round(values['base_amount'], 2),
                    'CuotaRepercutida': sign * float_round(values['tax_amount'], 2),
                }
                sujeta_no_sujeta\
                    .setdefault('Sujeta', {})\
                    .setdefault('NoExenta', {})\
                    .setdefault('DesgloseIVA', {'DetalleIVA': []})['DetalleIVA']\
                    .append(tax_info)
                if l10n_es_type == 'sujeto':
                    sujeto.append(tax_info)
                else:
                    sujeto_isp.append(tax_info)
            elif l10n_es_type == 'exento':
                sujeta_no_sujeta\
                    .setdefault('Sujeta', {})\
                    .setdefault('Exenta', {'DetalleExenta': []})['DetalleExenta']\
                    .append({
                        'BaseImponible': sign * float_round(values['base_amount'], 2),
                        'CausaExencion': grouping_key['l10n_es_exempt_reason'],
                    })
            elif l10n_es_type == 'recargo':
                detalle_iva = sujeta_no_sujeta\
                    .get('Sujeta', {})\
                    .get('NoExenta', {})\
                    .get('DesgloseIVA', {})\
                    .get('DetalleIVA')
                if detalle_iva:
                    detalle_iva[-1]['CuotaRecargoEquivalencia'] = sign * float_round(values['tax_amount'], 2)
                    detalle_iva[-1]['TipoRecargoEquivalencia'] = sign * grouping_key['applied_tax_amount']
            elif l10n_es_type == 'no_sujeto':
                no_sujeta = sujeta_no_sujeta.setdefault('NoSujeta', {})
                no_sujeta.setdefault('ImportePorArticulos7_14_Otros', 0.0)
                no_sujeta['ImportePorArticulos7_14_Otros'] += sign * float_round(values['base_amount'], 2)
            elif l10n_es_type == 'no_sujeto_loc':
                no_sujeta = sujeta_no_sujeta.setdefault('NoSujeta', {})
                no_sujeta.setdefault('ImporteTAIReglasLocalizacion', 0.0)
                no_sujeta['ImporteTAIReglasLocalizacion'] += sign * float_round(values['base_amount'], 2)

        if 'sujeto' in encountered_l10n_es_type and 'sujeto_isp' not in encountered_l10n_es_type:
            sujeta_no_sujeta['Sujeta']['NoExenta']['TipoNoExenta'] = 'S2'
        elif 'sujeto' not in encountered_l10n_es_type and 'sujeto_isp' in encountered_l10n_es_type:
            sujeta_no_sujeta['Sujeta']['NoExenta']['TipoNoExenta'] = 'S1'
        elif 'sujeto' in encountered_l10n_es_type and 'sujeto_isp' in encountered_l10n_es_type:
            sujeta_no_sujeta['Sujeta']['NoExenta']['TipoNoExenta'] = 'S3'

        return {
            'sujeta_no_sujeta': sujeta_no_sujeta,
            'sujeto': sujeto,
            'sujeto_isp': sujeto_isp,
        }