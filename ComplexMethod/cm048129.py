def _l10n_es_edi_get_invoices_info(self, invoices):
        eu_country_codes = set(self.env.ref('base.europe').country_ids.mapped('code'))

        info_list = []
        for invoice in invoices:
            com_partner = invoice.commercial_partner_id
            is_simplified = invoice.l10n_es_is_simplified

            info = {
                'PeriodoLiquidacion': {
                    'Ejercicio': str(invoice.date.year),
                    'Periodo': str(invoice.date.month).zfill(2),
                },
                'IDFactura': {
                    'FechaExpedicionFacturaEmisor': invoice.invoice_date.strftime('%d-%m-%Y'),
                },
            }

            if invoice.is_sale_document():
                invoice_node = info['FacturaExpedida'] = {}
            else:
                invoice_node = info['FacturaRecibida'] = {}

            # === Partner ===

            partner_info = self._l10n_es_edi_get_partner_info(com_partner)

            # === Invoice ===

            if invoice.delivery_date and invoice.delivery_date != invoice.invoice_date:
                invoice_node['FechaOperacion'] = invoice.delivery_date.strftime('%d-%m-%Y')
            invoice_node['DescripcionOperacion'] = invoice.invoice_origin[:500] if invoice.invoice_origin else 'manual'
            reagyp = invoice.invoice_line_ids.tax_ids.filtered(lambda t: t.l10n_es_type == 'sujeto_agricultura')
            if invoice.is_sale_document():
                nif = invoice.company_id.vat[2:] if invoice.company_id.vat.startswith('ES') else invoice.company_id.vat
                info['IDFactura']['IDEmisorFactura'] = {'NIF': nif}
                info['IDFactura']['NumSerieFacturaEmisor'] = invoice.name[:60]
                if not is_simplified:
                    invoice_node['Contraparte'] = {
                        **partner_info,
                        'NombreRazon': com_partner.name[:120],
                    }
                invoice_node['ClaveRegimenEspecialOTrascendencia'] = invoice.invoice_line_ids.tax_ids._l10n_es_get_regime_code()
            else:
                if invoice._l10n_es_is_dua():
                    partner_info = self._l10n_es_edi_get_partner_info(invoice.company_id.partner_id)
                info['IDFactura']['IDEmisorFactura'] = partner_info
                # In case of cancel
                info["IDFactura"]["IDEmisorFactura"].update(
                    {"NombreRazon": com_partner.name[0:120]}
                )
                info["IDFactura"]["NumSerieFacturaEmisor"] = (invoice.ref or "")[:60]
                if not is_simplified:
                    invoice_node['Contraparte'] = {
                        **partner_info,
                        'NombreRazon': com_partner.name[:120],
                    }

                if invoice.l10n_es_registration_date:
                    invoice_node['FechaRegContable'] = invoice.l10n_es_registration_date.strftime('%d-%m-%Y')
                else:
                    invoice_node['FechaRegContable'] = fields.Date.context_today(self).strftime('%d-%m-%Y')

                mod_303_10 = self.env.ref('l10n_es.mod_303_casilla_10_balance')._get_matching_tags()
                mod_303_11 = self.env.ref('l10n_es.mod_303_casilla_11_balance')._get_matching_tags()
                tax_tags = invoice.invoice_line_ids.tax_ids.repartition_line_ids.tag_ids
                intracom = bool(tax_tags & (mod_303_10 + mod_303_11))
                if intracom:
                    invoice_node['ClaveRegimenEspecialOTrascendencia'] = '09'
                elif reagyp:
                    invoice_node['ClaveRegimenEspecialOTrascendencia'] = '02'
                else:
                    invoice_node['ClaveRegimenEspecialOTrascendencia'] = '01'

            if invoice.move_type == 'out_invoice':
                invoice_node['TipoFactura'] = 'F2' if is_simplified else 'F1'
            elif invoice.move_type == 'out_refund':
                invoice_node['TipoFactura'] = 'R5' if is_simplified else 'R1'
                invoice_node['TipoRectificativa'] = 'I'
            elif invoice.move_type == 'in_invoice':
                if reagyp:
                    invoice_node['TipoFactura'] = 'F6'
                elif invoice._l10n_es_is_dua():
                    invoice_node['TipoFactura'] = 'F5'
                else:
                    invoice_node['TipoFactura'] = 'F1'
            elif invoice.move_type == 'in_refund':
                invoice_node['TipoFactura'] = 'R4'
                invoice_node['TipoRectificativa'] = 'I'

            # === Taxes ===

            sign = -1 if invoice.move_type in ('out_refund', 'in_refund') else 1

            if invoice.is_sale_document():
                # Customer invoices
                if not com_partner._l10n_es_is_foreign() or is_simplified:
                    tax_details_info_vals = self._l10n_es_edi_get_invoices_tax_details_info(invoice)
                    invoice_node['TipoDesglose'] = {'DesgloseFactura': tax_details_info_vals['tax_details_info']}

                    invoice_node['ImporteTotal'] = float_round(sign * (
                        tax_details_info_vals['tax_details']['base_amount']
                        + tax_details_info_vals['tax_details']['tax_amount']
                        - tax_details_info_vals['tax_amount_retention']
                    ), 2)
                else:
                    tax_details_info_service_vals = self._l10n_es_edi_get_invoices_tax_details_info(
                        invoice,
                        filter_invl_to_apply=lambda x: any(t.tax_scope == 'service' for t in x.tax_ids)
                    )
                    tax_details_info_consu_vals = self._l10n_es_edi_get_invoices_tax_details_info(
                        invoice,
                        filter_invl_to_apply=lambda x: any(t.tax_scope == 'consu' for t in x.tax_ids)
                    )

                    if tax_details_info_service_vals['tax_details_info']:
                        invoice_node.setdefault('TipoDesglose', {})
                        invoice_node['TipoDesglose'].setdefault('DesgloseTipoOperacion', {})
                        invoice_node['TipoDesglose']['DesgloseTipoOperacion']['PrestacionServicios'] = tax_details_info_service_vals['tax_details_info']
                    if tax_details_info_consu_vals['tax_details_info']:
                        invoice_node.setdefault('TipoDesglose', {})
                        invoice_node['TipoDesglose'].setdefault('DesgloseTipoOperacion', {})
                        invoice_node['TipoDesglose']['DesgloseTipoOperacion']['Entrega'] = tax_details_info_consu_vals['tax_details_info']

                    invoice_node['ImporteTotal'] = float_round(sign * (
                        tax_details_info_service_vals['tax_details']['base_amount']
                        + tax_details_info_service_vals['tax_details']['tax_amount']
                        - tax_details_info_service_vals['tax_amount_retention']
                        + tax_details_info_consu_vals['tax_details']['base_amount']
                        + tax_details_info_consu_vals['tax_details']['tax_amount']
                        - tax_details_info_consu_vals['tax_amount_retention']
                    ), 2)

            else:
                # Vendor bills

                tax_details_info_isp_vals = self._l10n_es_edi_get_invoices_tax_details_info(
                    invoice,
                    filter_invl_to_apply=lambda x: any(t for t in x.tax_ids if t.l10n_es_type == 'sujeto_isp'),
                )
                tax_details_info_other_vals = self._l10n_es_edi_get_invoices_tax_details_info(
                    invoice,
                    filter_invl_to_apply=lambda x: not any(t for t in x.tax_ids if t.l10n_es_type == 'sujeto_isp'),
                )

                invoice_node['DesgloseFactura'] = {}
                if tax_details_info_isp_vals['tax_details_info']:
                    invoice_node['DesgloseFactura']['InversionSujetoPasivo'] = tax_details_info_isp_vals['tax_details_info']
                if tax_details_info_other_vals['tax_details_info']:
                    invoice_node['DesgloseFactura']['DesgloseIVA'] = tax_details_info_other_vals['tax_details_info']

                if invoice._l10n_es_is_dua() or any(t.l10n_es_type == 'ignore' for t in invoice.invoice_line_ids.tax_ids):
                    invoice_node['ImporteTotal'] = float_round(sign * (
                            tax_details_info_isp_vals['tax_details']['base_amount']
                            + tax_details_info_isp_vals['tax_details']['tax_amount']
                            + tax_details_info_other_vals['tax_details']['base_amount']
                            + tax_details_info_other_vals['tax_details']['tax_amount']
                    ), 2)
                else: # Intra-community -100 repartition line needs to be taken into account
                    invoice_node['ImporteTotal'] = float_round(-invoice.amount_total_signed
                                                         - sign * tax_details_info_isp_vals['tax_amount_retention']
                                                         - sign * tax_details_info_other_vals['tax_amount_retention'], 2)

                invoice_node['CuotaDeducible'] = float_round(sign * (
                    tax_details_info_isp_vals['tax_amount_deductible']
                    + tax_details_info_other_vals['tax_amount_deductible']
                ), 2)

            info_list.append(info)
        return info_list