def _request_handler(cls, s: Session, r: PreparedRequest, /, **kw):
        response = Response()
        response.status_code = 200
        url = r.path_url.lower()
        if r.path_url.startswith('/api/peppol/1/lookup'):
            peppol_identifier = parse.parse_qs(r.path_url.rsplit('?')[1])['peppol_identifier'][0].lower()
            url_quoted_peppol_identifier = parse.quote_plus(peppol_identifier)
            if peppol_identifier == '0208:0477472701':
                response.status_code = 200
                response.json = lambda: {
                    "result": {
                        'identifier': peppol_identifier,
                        'smp_base_url': "http://iap-services.odoo.com",
                        'ttl': 60,
                        'service_group_url': f'http://iap-services.odoo.com/iso6523-actorid-upis%3A%3A{url_quoted_peppol_identifier}',
                        'services': [
                            {
                                "href": f"http://iap-services.odoo.com/iso6523-actorid-upis%3A%3A{url_quoted_peppol_identifier}/services/busdox-docid-qns%3A%3Aurn%3Aoasis%3Anames%3Aspecification%3Aubl%3Aschema%3Axsd%3AInvoice-2%3A%3AInvoice%23%23urn%3Acen.eu%3Aen16931%3A2017%23compliant%23urn%3Afdc%3Apeppol.eu%3A2017%3Apoacc%3Abilling%3A3.0%3A%3A2.1",
                                "document_id": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1",
                            },
                        ],
                    },
                }
                return response
            if peppol_identifier == '0208:2718281828':
                response.status_code = 200
                response.json = lambda: {
                    "result": {
                        'identifier': peppol_identifier,
                        'smp_base_url': "http://iap-services.odoo.com",
                        'ttl': 60,
                        'service_group_url': f'http://iap-services.odoo.com/iso6523-actorid-upis%3A%3A{url_quoted_peppol_identifier}',
                        'services': [
                            {
                                "href": f"http://iap-services.odoo.com/iso6523-actorid-upis%3A%3A{url_quoted_peppol_identifier}/services/busdox-docid-qns%3A%3Aurn%3Aoasis%3Anames%3Aspecification%3Aubl%3Aschema%3Axsd%3AInvoice-2%3A%3AInvoice%23%23urn%3Acen.eu%3Aen16931%3A2017%23compliant%23urn%3Afdc%3Apeppol.eu%3A2017%3Apoacc%3Abilling%3A3.0%3A%3A2.1",
                                "document_id": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1",
                            }
                        ],
                    },
                }
                return response

            if peppol_identifier in '0198:dk16356706':
                response.status_code = 200
                response.json = lambda: {"result": {
                        'identifier': peppol_identifier,
                        'smp_base_url': "http://iap-services.odoo.com",
                        'ttl': 60,
                        'service_group_url': f'http://iap-services.odoo.com/iso6523-actorid-upis%3A%3A{url_quoted_peppol_identifier}',
                        'services': [],
                    },
                }
                return response
            else:
                response.status_code = 404
                response.json = lambda: {"error": {"code": "NOT_FOUND", "message": "no naptr record", "retryable": False}}
                return response

        body = json.loads(r.body)
        if url == '/api/peppol/1/send_document':
            if not body['params']['documents']:
                raise UserError('No documents were provided')
            num_invoices = len(body['params']['documents'])
            response.json = lambda: {
                'result': {
                    'messages': [{'message_uuid': FAKE_UUID[0]}] * num_invoices
                }
            }
            return response

        if url == '/api/peppol/1/ack':
            response.json = lambda: {'result': {}}
            return response

        if url == '/api/peppol/1/get_all_documents':
            response.json = lambda: {
                'result': {
                    'messages': [
                        {
                            'accounting_supplier_party': '0198:dk16356706',
                            'filename': 'test_incoming.xml',
                            'uuid': FAKE_UUID[1],
                            'state': 'done',
                            'direction': 'incoming',
                            'document_type': 'Invoice',
                            'sender': '0198:dk16356706',
                            'receiver': '0208:0477472701',
                            'timestamp': '2022-12-30',
                            'error': False if not cls.env.context.get('error') else 'Test error',
                        }
                    ],
                }
            }
            return response

        if url == '/api/peppol/1/get_document':
            uuid = body['params']['message_uuids'][0]
            response_content = {}
            if uuid == FAKE_UUID[0]:
                response_content = {
                    'accounting_supplier_party': False,
                    'filename': 'test_outgoing.xml',
                    'enc_key': '',
                    'document': '',
                    'state': 'done' if not cls.env.context.get('error') else 'error',
                    'direction': 'outgoing',
                    'document_type': 'Invoice',
                }
            elif uuid == FAKE_UUID[1]:
                response_content = {
                    'accounting_supplier_party': '0198:dk16356706',
                    'filename': 'test_incoming',
                    'enc_key': file_open(f'{FILE_PATH}/enc_key', mode='rb').read(),
                    'document': b64encode(file_open(f'{FILE_PATH}/{cls.mocked_incoming_invoice_fname}', mode='rb').read()),
                    'state': 'done' if not cls.env.context.get('error') else 'error',
                    'direction': 'incoming',
                    'document_type': 'Invoice',
                    'origin_message_uuid': FAKE_UUID[1],
                }

            response.json = lambda: {'result': {uuid: response_content}}
            return response

        if url == '/api/peppol/1/send_response':
            # This will be called if account_peppol_response is installed, to be overridden in that module
            num_responses = len(body['params']['reference_uuids'])
            response.json = lambda: {
                'result': {
                    'messages': [{'message_uuid': 'rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr'}] * num_responses,
                },
            }
            return response

        return super()._request_handler(s, r, **kw)