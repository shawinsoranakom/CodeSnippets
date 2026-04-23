def _l10n_ro_edi_stock_get_template_data(self, data: dict):
        """
        Returns the data necessary to render the eTransport template
        """
        commercial_partner = data['partner_id'].commercial_partner_id
        transport_partner = data['transport_partner_id']
        company_id = data['company_id']
        scheduled_date = data['scheduled_date'].date()
        name = data['name']
        commercial_partner_code = None

        if commercial_partner.vat:
            commercial_partner_code = self._l10n_ro_edi_stock_get_cod(commercial_partner)
        elif self.l10n_ro_edi_stock_operation_type == '30':
            commercial_partner_code = 'PF'

        template_data = {
            'send_type': data['send_type'],
            'codDeclarant': self._l10n_ro_edi_stock_get_cod(company_id),
            'refDeclarant': name,
            'notificare': {
                'codTipOperatiune': data['l10n_ro_edi_stock_operation_type'],
                'bunuriTransportate': [
                    {
                        'codScopOperatiune': data['l10n_ro_edi_stock_operation_scope'],
                        'codTarifar': (product.intrastat_code_id.code if 'intrastat_code_id' in product._fields else None) or '00000000',
                        'denumireMarfa': product.name,
                        'cantitate': float_round(move.product_qty, precision_digits=2),
                        'codUnitateMasura': move.product_uom._get_unece_code(),
                        'greutateNeta': float_round(move.weight, precision_digits=2),
                        'greutateBruta': float_round(self._l10n_ro_edi_stock_get_gross_weight(move), precision_digits=2),
                        'valoareLeiFaraTva': float_round(product.standard_price, precision_digits=2),
                    }
                    for move in data['stock_move_ids'] for product in move.product_id
                ],
                'partenerComercial': {
                    'codTara': _eu_country_vat.get(commercial_partner.country_code, commercial_partner.country_code),
                    'denumire': commercial_partner.name,
                    'cod': commercial_partner_code,
                },
                'dateTransport': {
                    'nrVehicul': data['l10n_ro_edi_stock_vehicle_number'].upper(),
                    'nrRemorca1': data['l10n_ro_edi_stock_trailer_1_number'].upper() if data['l10n_ro_edi_stock_trailer_1_number'] else None,
                    'nrRemorca2': data['l10n_ro_edi_stock_trailer_2_number'].upper() if data['l10n_ro_edi_stock_trailer_2_number'] else None,
                    'codTaraOrgTransport': _eu_country_vat.get(transport_partner.country_code, transport_partner.country_code),
                    'codOrgTransport': self._l10n_ro_edi_stock_get_cod(transport_partner),
                    'denumireOrgTransport': transport_partner.name,
                    'dataTransport': scheduled_date,
                },
                'locStartTraseuRutier': {
                    'location_type': data['l10n_ro_edi_stock_start_loc_type'],
                },
                'locFinalTraseuRutier': {
                    'location_type': data['l10n_ro_edi_stock_end_loc_type'],
                },
                'documenteTransport': {
                    'tipDocument': "30",
                    'dataDocument': scheduled_date,
                    'numarDocument': name,
                    'observatii': data['l10n_ro_edi_stock_remarks'],
                }
            },
        }

        if data['send_type'] == 'amend':
            template_data['notificare']['uit'] = data['l10n_ro_edi_stock_document_uit']

        for loc in ('start', 'end'):
            key = 'locStartTraseuRutier' if loc == 'start' else 'locFinalTraseuRutier'

            match template_data['notificare'][key]['location_type']:
                case 'location':
                    match data['picking_type_id'].code:
                        case 'outgoing':
                            partner = data['picking_type_id'].warehouse_id.partner_id if loc == 'start' else data['partner_id']
                        case 'incoming':
                            partner = data['picking_type_id'].warehouse_id.partner_id if loc == 'end' else data['partner_id']

                    template_data['notificare'][key]['locatie'] = {
                        'codJudet': STATE_CODES[partner.state_id.code],
                        'denumireLocalitate': partner.city,
                        'denumireStrada': partner.street,
                        'codPostal': partner.zip,
                        'alteInfo': partner.street2,
                    }
                case 'bcp':
                    template_data['notificare'][key]['codPtf'] = data[f'l10n_ro_edi_stock_{loc}_bcp']
                case 'customs':
                    template_data['notificare'][key]['codBirouVamal'] = data[f'l10n_ro_edi_stock_{loc}_customs_office']

        return {'data': template_data}