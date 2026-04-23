def _l10n_es_edi_call_web_service_sign_common(self, invoices, info_list, cancel=False):
        company = invoices.company_id

        # All are sharing the same value.
        csv_number = invoices.mapped('l10n_es_edi_csv')[0]

        # Set registration date
        invoices.filtered(lambda inv: not inv.l10n_es_registration_date).write({
            'l10n_es_registration_date': fields.Date.context_today(self),
        })

        # === Call the web service ===

        # Get connection data.
        l10n_es_sii_tax_agency = company.mapped('l10n_es_sii_tax_agency')[0]
        connection_vals = getattr(self, f'_l10n_es_edi_web_service_{l10n_es_sii_tax_agency}_vals')(invoices)

        header = {
            'IDVersionSii': '1.1',
            'Titular': {
                'NombreRazon': company.name[:120],
                'NIF': company.vat[2:] if company.vat.startswith('ES') else company.vat,
            },
            'TipoComunicacion': 'A1' if csv_number else 'A0',
        }

        session = requests.Session()
        session.cert = company.l10n_es_sii_certificate_id
        session.mount('https://', CertificateAdapter(ciphers=EUSKADI_CIPHERS))

        client = zeep.Client(connection_vals['url'], operation_timeout=60, timeout=60, session=session)

        if invoices[0].is_sale_document():
            service_name = 'SuministroFactEmitidas'
        else:
            service_name = 'SuministroFactRecibidas'
        if company.l10n_es_sii_test_env and not connection_vals.get('test_url'):
            service_name += 'Pruebas'

        # Establish the connection.
        serv = client.bind('siiService', service_name)
        if company.l10n_es_sii_test_env and connection_vals.get('test_url'):
            serv._binding_options['address'] = connection_vals['test_url']

        error_msg = None
        try:
            if cancel:
                if invoices[0].is_sale_document():
                    res = serv.AnulacionLRFacturasEmitidas(header, info_list)
                else:
                    res = serv.AnulacionLRFacturasRecibidas(header, info_list)
            else:
                if invoices[0].is_sale_document():
                    res = serv.SuministroLRFacturasEmitidas(header, info_list)
                else:
                    res = serv.SuministroLRFacturasRecibidas(header, info_list)
        except requests.exceptions.SSLError as error:
            error_msg = _("The SSL certificate could not be validated.")
        except (zeep.exceptions.Error, requests.exceptions.ConnectionError) as error:
            error_msg = _("Networking error:\n%s", error)
        except Exception as error:
            error_msg = str(error)

        if error_msg:
            return {inv: {
                'error': error_msg,
                'blocking_level': 'warning',
            } for inv in invoices}

        # Process response.

        if not res or not res.RespuestaLinea:
            return {inv: {
                'error': _("The web service is not responding"),
                'blocking_level': 'warning',
            } for inv in invoices}

        resp_state = res["EstadoEnvio"]
        l10n_es_edi_csv = res['CSV']

        if resp_state == 'Correcto':
            invoices.write({'l10n_es_edi_csv': l10n_es_edi_csv})
            return {inv: {'success': True} for inv in invoices}

        results = {}
        for respl in res.RespuestaLinea:
            invoice_number = respl.IDFactura.NumSerieFacturaEmisor

            # Retrieve the corresponding invoice.
            # Note: ref can be the same for different partners but there is no enough information on the response
            # to match the partner.

            # Note: Invoices are batched per move_type.
            if invoices[0].is_sale_document():
                inv = invoices.filtered(lambda x: x.name[:60] == invoice_number)
            else:
                # 'ref' can be the same for different partners.
                candidates = invoices.filtered(lambda x: x.ref[:60] == invoice_number)
                if len(candidates) > 1:
                    respl_partner_info = respl.IDFactura.IDEmisorFactura
                    inv = None
                    for candidate in candidates:
                        partner = candidate.commercial_partner_id
                        if candidate._l10n_es_is_dua():
                            partner = candidate.company_id.partner_id
                        partner_info = self._l10n_es_edi_get_partner_info(partner)
                        if partner_info.get('NIF') and partner_info['NIF'] == respl_partner_info.NIF:
                            inv = candidate
                            break
                        if (
                            partner_info.get('IDOtro')
                            and respl_partner_info['IDOtro']
                            and all(respl_partner_info['IDOtro'][k] == v for k, v in partner_info['IDOtro'].items())
                        ):
                            inv = candidate
                            break

                    if not inv:
                        # This case shouldn't happen and means there is something wrong in this code. However, we can't
                        # raise anything since the document has already been approved by the government. The result
                        # will only be a badly logged message into the chatter so, not a big deal.
                        inv = candidates[0]
                else:
                    inv = candidates

            resp_line_state = respl.EstadoRegistro
            respl_dict = dict(respl)
            if resp_line_state in ('Correcto', 'AceptadoConErrores'):
                inv.l10n_es_edi_csv = l10n_es_edi_csv
                results[inv] = {'success': True}
                if resp_line_state == 'AceptadoConErrores':
                    inv.message_post(body=_("This was accepted with errors: ") + html_escape(respl.DescripcionErrorRegistro))
            elif (
                (respl_dict.get('RegistroDuplicado') and respl.RegistroDuplicado.EstadoRegistro == 'Correcta')
                or
                (cancel and respl_dict.get('CodigoErrorRegistro') == 3001)
            ):
                results[inv] = {'success': True}
                inv.message_post(body=_("We saw that this invoice was sent correctly before, but we did not treat "
                                        "the response.  Make sure it is not because of a wrong configuration."))

            elif respl.CodigoErrorRegistro == 1117 and not self.env.context.get('error_1117'):
                return self.with_context(error_1117=True)._l10n_es_edi_sii_post_invoices(invoices)


            else:
                results[inv] = {
                    'error': _("[%(error_code)s] %(error_message)s", error_code=respl.CodigoErrorRegistro, error_message=respl.DescripcionErrorRegistro),
                    'blocking_level': 'error',
                }

        return results