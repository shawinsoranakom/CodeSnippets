def _send_batch(self, batch_dict):
        info = {
            'errors': [],
            'record_info': {},
            'soap_fault': False,
        }
        errors = info['errors']
        record_info = info['record_info']

        try:
            register, zeep_info = _get_zeep_operation(self.env.company, 'registration')
        except (zeep.exceptions.Error, requests.exceptions.RequestException) as error:
            errors.append(_("Networking error:\n%s", error))
            return info

        try:
            res = register(batch_dict['Cabecera'], batch_dict['RegistroFactura'])
            # `res` is of type 'zeep.client.SerialProxy'
        except requests.exceptions.SSLError:
            errors.append(_("The SSL certificate could not be validated."))
        except zeep.exceptions.TransportError as error:
            certificate_error = "No autorizado. Se ha producido un error al verificar el certificado presentado"
            if certificate_error in error.message:
                errors.append(_("The document could not be sent; the access was denied due to a problem with the certificate."))
            else:
                errors.append(_("Networking error while sending the document:\n%s", error))
        except requests.exceptions.ReadTimeout as error:
            # The error is only partially translated since we check for this message for the timeout duplicate handling.
            # (See `_send_as_batch`)
            error_description = _("Timeout while waiting for the response from the server:\n%s", error)
            errors.append(f"[Read-Timeout] {error_description}")
        except requests.exceptions.RequestException as error:
            errors.append(_("Networking error while sending the document:\n%s", error))
        except zeep.exceptions.Fault as soapfault:
            info['soap_fault'] = True
            errors.append(f"[{soapfault.code}] {soapfault.message}")
        except zeep.exceptions.XMLSyntaxError as error:
            _logger.error("raw zeep response:\n%s", zeep_info.get('raw_response'))
            certificate_error = "The root element found is html"
            if certificate_error in error.message:
                errors.append(_("The response of the server had the wrong format (HTML instead of XML). It is most likely a problem with the certificate."))
            else:
                errors.append(_("Error while sending the batch document:\n%s", error))
        except zeep.exceptions.Error as error:
            _logger.error("raw zeep response:\n%s", zeep_info.get('raw_response'))
            errors.append(_("Error while sending the batch document:\n%s", error))

        if errors:
            return info

        info.update({
            'response_csv': res['CSV'] if 'CSV' in res else None,  # noqa: SIM401 - `res` is of type 'zeep.client.SerialProxy'
            'waiting_time_seconds': int(res['TiempoEsperaEnvio']),
        })

        # EstadoRegistroType
        state_map = {
            'Incorrecto': 'rejected',
            'AceptadoConErrores': 'registered_with_errors',
            'Correcto': 'accepted',
        }
        # EstadoRegistroSFType
        duplicate_state_map = {
            'AceptadaConErrores': 'registered_with_errors',
            'Correcta': 'accepted',
            'Anulada': 'cancelled',
        }

        for response_line in res['RespuestaLinea']:
            record_id = response_line['IDFactura']
            invoice_issuer = record_id['IDEmisorFactura'].strip()
            invoice_name = record_id['NumSerieFactura'].strip()
            record_key = str((invoice_issuer, invoice_name))

            operation_type = response_line['Operacion']['TipoOperacion']
            received_state = response_line['EstadoRegistro']
            # In case of a duplicate the response supplies information about the original invoice.
            duplicate_info = response_line['RegistroDuplicado']
            duplicate = {}
            if duplicate_info:
                duplicate_state = duplicate_state_map[duplicate_info['EstadoRegistroDuplicado']]
                duplicate = {
                    'state': duplicate_state,
                    'errors': [],
                }
                if duplicate_state in ('rejected', 'registered_with_errors'):
                    error_code = duplicate_info['CodigoErrorRegistro']
                    error_description = duplicate_info['DescripcionErrorRegistro']
                    duplicate['errors'].append(f"[{error_code}] {error_description}")

            state = state_map[received_state]
            errors = []
            if state in ('rejected', 'registered_with_errors'):
                error_code = response_line['CodigoErrorRegistro']
                error_description = response_line['DescripcionErrorRegistro']
                errors.append(f"[{error_code}] {error_description}")

            record_info[record_key] = {
                'state': state,
                'cancellation': operation_type == 'Anulacion',
                'errors': errors,
                'duplicate': duplicate,
            }

        return info