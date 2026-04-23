def _render_vals_operation(self, vals):
        company_values = vals['company'].partner_id._l10n_es_edi_verifactu_get_values()
        invoice_date = self._format_date_type(vals['invoice_date'])

        if vals['cancellation']:
            render_vals = {
                'IDFactura': {
                    'IDEmisorFacturaAnulada': company_values['NIF'],
                    'NumSerieFacturaAnulada': vals['name'],
                    'FechaExpedicionFacturaAnulada': invoice_date,
                }
            }
            return render_vals

        render_vals = {
            'NombreRazonEmisor': company_values['NombreRazon'],
            'IDFactura': {
                'IDEmisorFactura': company_values['NIF'],
                'NumSerieFactura': vals['name'],
                'FechaExpedicionFactura': invoice_date,
            }
        }

        rectified_document = vals['refunded_document'] or vals['substituted_document']
        if vals['verifactu_move_type'] == 'invoice':
            tipo_rectificativa = None
            tipo_factura = 'F2' if vals['is_simplified'] else 'F3' if vals.get('was_simplified_invoice') else 'F1'
            delivery_date = self._format_date_type(vals['delivery_date'])
            fecha_operacion = delivery_date if delivery_date and delivery_date != invoice_date else None
        elif vals['verifactu_move_type'] == 'reversal_for_substitution':
            tipo_rectificativa = None
            tipo_factura = 'F2' if vals['is_simplified'] else 'F1'
            fecha_operacion = None
        elif vals['verifactu_move_type'] == 'correction_substitution':
            tipo_rectificativa = 'S'
            tipo_factura = vals['refund_reason']
            rectified = rectified_document._get_record_identifier()
            fecha_operacion = rectified['FechaOperacion'] or rectified['FechaExpedicionFactura']
        else:
            # vals['verifactu_move_type'] == 'correction_incremental':
            tipo_rectificativa = 'I'
            tipo_factura = vals['refund_reason']
            rectified = rectified_document._get_record_identifier()
            fecha_operacion = rectified['FechaOperacion'] or rectified['FechaExpedicionFactura']

        # Note: Error [1189]
        # Si TipoFactura es F1 o F3 o R1 o R2 o R3 o R4 el bloque Destinatarios tiene que estar cumplimentado.

        if not vals['is_simplified']:
            render_vals['Destinatarios'] = {
                'IDDestinatario': [vals['partner']._l10n_es_edi_verifactu_get_values()]
            }

        render_vals.update({
            'TipoFactura': tipo_factura,
            'TipoRectificativa': tipo_rectificativa,  # may be None
            'FechaOperacion': fecha_operacion,
            'DescripcionOperacion': vals['description'] or 'manual',
        })

        if vals['verifactu_move_type'] in ('correction_incremental', 'correction_substitution'):
            rectified_record_identifier = rectified_document._get_record_identifier()
            render_vals.update({
                'FacturasRectificadas': [{
                    'IDFacturaRectificada': {
                        key: rectified_record_identifier[key]
                        for key in ['IDEmisorFactura', 'NumSerieFactura', 'FechaExpedicionFactura']
                    }
                }],
            })
        # [1118] Si la factura es de tipo rectificativa por sustitución el bloque ImporteRectificacion es obligatorio.
        if vals['verifactu_move_type'] == 'correction_substitution':
            # We only support substitution if we also send an invoice that cancels out the amounts of the original invoice.
            # ('Opción 2' in the FAQ under '¿Cómo registra el emisor una factura rectificativa por sustitución “S”?')
            render_vals.update({
                'ImporteRectificacion': {
                    'BaseRectificada': self._round_format_number_2(0),
                    'CuotaRectificada': self._round_format_number_2(0),
                },
            })

        return render_vals