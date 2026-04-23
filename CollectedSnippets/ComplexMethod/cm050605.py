def _request_handler(cls, s: Session, r: PreparedRequest, /, **kw):
        response = Response()
        url = r.path_url.lower()
        if r.path_url.startswith('/api/peppol/1/lookup'):
            peppol_identifier = parse.parse_qs(r.path_url.rsplit('?')[1])['peppol_identifier'][0].lower()
            if peppol_identifier in {'0088:9482348239847239874', '9932:gb1232434'}:
                url_quoted_peppol_identifier = parse.quote_plus(peppol_identifier)
                response.status_code = 200
                response.json = lambda: {"result": {
                    'identifier': peppol_identifier,
                    'smp_base_url': "http://iap-services.odoo.com",
                    'ttl': 60,
                    'service_group_url': f'http://iap-services.odoo.com/iso6523-actorid-upis%3A%3A{url_quoted_peppol_identifier}',
                    'services': [
                        {
                            "href": "https://peppol-smp-test.odoo.com/iso6523-actorid-upis%3A%3A0009%3A53346824500022/services/busdox-docid-qns%3A%3Aurn%3Aoasis%3Anames%3Aspecification%3Aubl%3Aschema%3Axsd%3AInvoice-2%3A%3AInvoice%23%23urn%3Acen.eu%3Aen16931%3A2017%23compliant%23urn%3Afdc%3Apeppol.eu%3A2017%3Apoacc%3Abilling%3A3.0%3A%3A2.1",
                            "document_id": "busdox-docid-qns::urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1"
                        }, {
                            "href": "https://peppol-smp-test.odoo.com/iso6523-actorid-upis%3A%3A0009%3A53346824500022/services/busdox-docid-qns%3A%3Aurn%3Aoasis%3Anames%3Aspecification%3Aubl%3Aschema%3Axsd%3AApplicationResponse-2%3A%3AApplicationResponse%23%23urn%3Acen.eu%3Aen16931%3A2017%23compliant%23urn%3Afdc%3Apeppol.eu%3A2017%3Apoacc%3Aselfbilling%3A3.0%3A%3A2.1",
                            "document_id": "busdox-docid-qns::urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2::ApplicationResponse##urn:fdc:peppol.eu:poacc:trns:invoice_response:3::2.1"
                        },
                    ],
                }}
                return response
        if url == '/api/peppol/1/send_response':
            body = json.loads(r.body)
            response.status_code = 200
            response.json = lambda: {'result': {
                'messages': [{'message_uuid': FAKE_OUTGOING_RESPONSE_UUID[body['params']['status']]}] * len(body['params']['reference_uuids'])
            }}
            return response

        if url == '/api/peppol/1/get_document':
            response = super()._request_handler(s, r, **kw)
            results = response.json()['result']
            body = json.loads(r.body)
            uuids = body['params']['message_uuids']
            enc_key = file_open(f'{RESPONSE_FILE_PATH}/enc_key', mode='rb').read()
            results.update({
                **{
                    FAKE_OUTGOING_RESPONSE_UUID[code]: {
                        'accounting_supplier_party': False,
                        'filename': 'test_outgoing.xml',
                        'enc_key': '',
                        'document': '',
                        'state': 'done' if not cls.env.context.get('error') else 'error',
                        'direction': 'outgoing',
                        'document_type': 'ApplicationResponse',
                        'origin_message_uuid': 'not_used_when_fetching_status',
                    } for code in FAKE_OUTGOING_RESPONSE_UUID
                },
                FAKE_INCOMING_RESPONSE_UUID: {
                    'accounting_supplier_party': False,
                    'filename': 'test_incoming_resp.xml',
                    'enc_key': enc_key,
                    'document': b64encode(cls._get_incoming_response_content()),
                    'state': 'done' if not cls.env.context.get('error') else 'error',
                    'direction': 'incoming',
                    'document_type': 'ApplicationResponse',
                    'origin_message_uuid': 'move_uuid_that_does_not_exist_on_user_db',
                }
            })
            response.json = lambda: {
                'result': {
                    uuid: results[uuid] for uuid in uuids
                }
            }
            return response

        if url == '/api/peppol/1/get_all_documents':
            response = super()._request_handler(s, r, **kw)
            json_content = response.json()
            json_content['result']['messages'].append({
                'accounting_supplier_party': '0198:dk16356706',
                'filename': 'test_incoming_resp.xml',
                'uuid': FAKE_INCOMING_RESPONSE_UUID,
                'state': 'done',
                'direction': 'incoming',
                'document_type': 'ApplicationResponse',
                'sender': '0198:dk16356706',
                'receiver': '0208:0477472701',
                'timestamp': '2022-12-30',
                'error': False if not cls.env.context.get('error') else 'Test error',
                'business_type': 'AP',
            })
            response.json = lambda: json_content
            return response
        return super()._request_handler(s, r, **kw)