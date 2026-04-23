def _render_vals_monetary_amounts(self, vals):
        # Note: We only support a single verifactu tax applicabilty, clave regimen pair per record.
        # For moves the clave regime is stored on each move in field `l10n_es_edi_verifactu_clave_regimen`
        if vals['cancellation']:
            return {}

        sign = vals['sign']
        sujeto_tax_types = self.env['account.tax']._l10n_es_get_sujeto_tax_types()

        recargo_tax_details_key = {}  # dict (tax_key -> recargo_tax_key)
        for record_tax_details in vals['tax_details']['tax_details_per_record'].values():
            main_key = None
            recargo_key = None
            # Note: There is only a single (main tax, recargo tax) pair on a single invoice line
            #       (if any; see `_check_record_values`)
            for key in record_tax_details:
                if key['recargo_taxes']:
                    main_key = key
                if key['l10n_es_type'] == 'recargo':
                    recargo_key = key
                if main_key and recargo_key:
                    break
            recargo_tax_details_key[main_key] = recargo_key

        detalles = []
        for key, tax_detail in vals['tax_details']['tax_details'].items():
            tax_type = key['l10n_es_type']
            # Tax types 'ignore' and 'retencion' are ignored when generating the `tax_details`
            # See `filter_to_apply` in function `_l10n_es_edi_verifactu_get_tax_details_functions` on 'account.tax'
            if tax_type == 'recargo':
                # Recargo taxes are only used in combination with another tax (a sujeto tax)
                # They will be handled when processing the remaining taxes
                continue

            exempt_reason = key['l10n_es_exempt_reason']  # only set if exempt

            tax_percentage = key['amount']
            base_amount = sign * tax_detail['base_amount']
            tax_amount = math.copysign(tax_detail['tax_amount'], base_amount)

            calificacion_operacion = None  # Reported if not tax-exempt;
            recargo_equivalencia = {}
            if tax_type in sujeto_tax_types:
                calificacion_operacion = 'S2' if tax_type == 'sujeto_isp' else 'S1'
                if key['recargo_taxes']:
                    recargo_key = recargo_tax_details_key.get(key)
                    recargo_tax_detail = vals['tax_details']['tax_details'][recargo_key]
                    recargo_tax_percentage = recargo_key['amount']
                    recargo_tax_amount = math.copysign(recargo_tax_detail['tax_amount'], base_amount)
                    recargo_equivalencia.update({
                        'tax_percentage': recargo_tax_percentage,
                        'tax_amount': recargo_tax_amount,
                    })
            elif tax_type in ('no_sujeto', 'no_sujeto_loc'):
                calificacion_operacion = 'N2' if tax_type == 'no_sujeto_loc' else 'N1'
            else:
                # tax_type == 'exento' (see `_check_record_values`)
                # exempt_reason set already
                # [1238]
                #     Si la operacion es exenta no se puede informar ninguno de los campos
                #     TipoImpositivo, CuotaRepercutida, TipoRecargoEquivalencia y CuotaRecargoEquivalencia.
                tax_percentage = None
                tax_amount = None
                recargo_percentage = None
                recargo_amount = None

            recargo_percentage = recargo_equivalencia.get('tax_percentage')
            recargo_amount = recargo_equivalencia.get('tax_amount')

            # Note on the TipoImpositivo and CuotaRepercutida tags.
            # In some cases it makes a difference for the validation whether the tags are output with 0
            # or not at all:
            # - In the no sujeto cases (calification_operacion in ('N1', 'N2')) we may not include them.
            # - In the (calification_operacion == S2) case the tags have to be included with value 0.
            #
            # See the following errors:
            # [1198]
            #     Si CalificacionOperacion es S2 TipoImpositivo y CuotaRepercutida deberan tener valor 0.
            # [1237]
            #     El valor del campo CalificacionOperacion está informado como N1 o N2 y el impuesto es IVA.
            #     No se puede informar de los campos TipoImpositivo, CuotaRepercutida, TipoRecargoEquivalencia y CuotaRecargoEquivalencia.
            if calificacion_operacion in ('N1', 'N2') and vals['l10n_es_applicability'] == '01':
                tax_percentage = None
                tax_amount = None

            detalle = {
                'Impuesto': vals['l10n_es_applicability'],
                'ClaveRegimen': vals['clave_regimen'],
                'CalificacionOperacion': calificacion_operacion,
                'OperacionExenta': exempt_reason,
                'TipoImpositivo': self._round_format_number_2(tax_percentage),
                'BaseImponibleOimporteNoSujeto': self._round_format_number_2(base_amount),
                'CuotaRepercutida': self._round_format_number_2(tax_amount),
                'TipoRecargoEquivalencia': self._round_format_number_2(recargo_percentage),
                'CuotaRecargoEquivalencia': self._round_format_number_2(recargo_amount),
            }

            detalles.append(detalle)

        total_amount = sign * (vals['tax_details']['base_amount'] + vals['tax_details']['tax_amount'])
        tax_amount = sign * (vals['tax_details']['tax_amount'])

        render_vals = {
            'Macrodato': 'S' if abs(total_amount) >= 100000000 else None,
            'Desglose': {
                'DetalleDesglose': detalles
            },
            'CuotaTotal': self._round_format_number_2(tax_amount),
            'ImporteTotal': self._round_format_number_2(total_amount),
        }

        return render_vals