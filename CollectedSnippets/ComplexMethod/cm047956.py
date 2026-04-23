def do_query_transaction_status(self, credentials, transaction_code, return_original_request=False):
        """ Query the status of a transaction.

        :param transaction_code: the code of the transaction to query
        :param return_original_request: whether to request the submitted invoice XML.
        :return: a list of dicts {'index': str, 'invoice_status': str, 'business_validation_messages', 'technical_validation_messages'}
        :raise: L10nHuEdiConnectionError
        """
        if credentials['mode'] == 'demo':
            invoices = self.env['account.move'].search([('l10n_hu_edi_transaction_code', '=', transaction_code)])
            if any(m.l10n_hu_edi_state.startswith('cancel') for m in invoices):
                return {
                    'processing_results': [
                        {
                            'index': str(i + 1),
                            'invoice_status': 'DONE',
                            'business_validation_messages': [{
                                'validation_result_code': 'INFO',
                                'validation_error_code': 'INFO_SINGLE_INVOICE_ANNULMENT',
                                'message': 'Egyedi számla technikai érvénytelenítése',
                            }],
                            'technical_validation_messages': [],
                        }
                        for i in range(len(invoices))
                    ],
                    'annulment_status': 'VERIFICATION_DONE',
                }
            else:
                return {
                    'processing_results': [
                        {
                            'index': str(i + 1),
                            'invoice_status': 'DONE',
                            'business_validation_messages': [],
                            'technical_validation_messages': [],
                        }
                        for i in range(len(invoices))
                    ],
                    'annulment_status': None,
                }

        template_values = {
            **self._get_header_values(credentials),
            'transactionId': transaction_code,
            'returnOriginalRequest': return_original_request,
        }
        request_data = self.env['ir.qweb']._render('l10n_hu_edi.query_transaction_status_request', template_values)
        request_data = etree.tostring(cleanup_xml_node(request_data, remove_blank_nodes=False), xml_declaration=True, encoding='UTF-8')

        response_xml = self._call_nav_endpoint(credentials['mode'], 'queryTransactionStatus', request_data)
        self._parse_error_response(response_xml)

        results = {
            'processing_results': [],
            'annulment_status': response_xml.findtext('api:processingResults/api:annulmentData/api:annulmentVerificationStatus', namespaces=XML_NAMESPACES),
        }
        for processing_result_xml in response_xml.iterfind('api:processingResults/api:processingResult', namespaces=XML_NAMESPACES):
            processing_result = {
                'index': processing_result_xml.findtext('api:index', namespaces=XML_NAMESPACES),
                'invoice_status': processing_result_xml.findtext('api:invoiceStatus', namespaces=XML_NAMESPACES),
                'business_validation_messages': [],
                'technical_validation_messages': [],
            }
            for message_xml in processing_result_xml.iterfind('api:businessValidationMessages', namespaces=XML_NAMESPACES):
                processing_result['business_validation_messages'].append({
                    'validation_result_code': message_xml.findtext('api:validationResultCode', namespaces=XML_NAMESPACES),
                    'validation_error_code': message_xml.findtext('api:validationErrorCode', namespaces=XML_NAMESPACES),
                    'message': message_xml.findtext('api:message', namespaces=XML_NAMESPACES),
                })
            for message_xml in processing_result_xml.iterfind('api:technicalValidationMessages', namespaces=XML_NAMESPACES):
                processing_result['technical_validation_messages'].append({
                    'validation_result_code': message_xml.findtext('common:validationResultCode', namespaces=XML_NAMESPACES),
                    'validation_error_code': message_xml.findtext('common:validationErrorCode', namespaces=XML_NAMESPACES),
                    'message': message_xml.findtext('common:message', namespaces=XML_NAMESPACES),
                })
            if return_original_request:
                try:
                    original_file = b64decode(processing_result_xml.findtext('api:originalRequest', namespaces=XML_NAMESPACES))
                    original_xml = etree.fromstring(original_file)
                except binascii.Error as e:
                    raise L10nHuEdiConnectionError(str(e)) from e
                except etree.ParserError as e:
                    raise L10nHuEdiConnectionError(str(e)) from e

                processing_result.update({
                    'original_file': original_file.decode(),
                    'original_xml': original_xml,
                })

            results['processing_results'].append(processing_result)

        return results