def _request_handler(cls, s: Session, r: PreparedRequest, /, **kw):
        response = Response()
        response.status_code = 200
        if r.path_url.startswith('/api/peppol/1/lookup'):
            nemhandel_identifier = parse.parse_qs(r.path_url.rsplit('?')[1])['peppol_identifier'][0].lower()
            url_quoted_nemhandel_identifier = parse.quote_plus(nemhandel_identifier)
            if nemhandel_identifier.endswith('12345674'):
                response.status_code = 404
                response.json = lambda: {"error": {"code": "NOT_FOUND", "message": "no naptr record", "retryable": False}}
                return response
            if nemhandel_identifier.endswith('12345666'):
                response.status_code = 200
                response.json = lambda: {
                    "result": {
                        'identifier': nemhandel_identifier,
                        'smp_base_url': "https://smp-demo.nemhandel.dk",
                        'ttl': 60,
                        'service_group_url': f'http:///smp-demo.nemhandel.dk/iso6523-actorid-upis%3A%3A{url_quoted_nemhandel_identifier}',
                        'services': [
                            {
                                "href": f"https://smp-demo.nemhandel.dk/iso6523-actorid-upis%3A%3A{url_quoted_nemhandel_identifier}/services/busdox-docid-qns%3A%3Aurn%3Aoasis%3Anames%3Aspecification%3Aubl%3Aschema%3Axsd%3ACreditNote-2%3A%3ACreditNote%23%23OIOUBL-2.1%3A%3A2.1",
                                "document_id": "busdox-docid-qns::urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##OIOUBL-2.1::2.1",
                            },
                        ],
                    },
                }
                return response
            if nemhandel_identifier.endswith('16356706'):
                response.status_code = 200
                response.json = lambda: {
                    "result": {
                        'identifier': nemhandel_identifier,
                        'smp_base_url': "https://smp-demo.nemhandel.dk",
                        'ttl': 60,
                        'service_group_url': f'http:///smp-demo.nemhandel.dk/iso6523-actorid-upis%3A%3A{url_quoted_nemhandel_identifier}',
                        'services': [],
                    },
                }
                return response
            response.status_code = 200
            response.json = lambda: {
                "result": {
                    'identifier': nemhandel_identifier,
                    'smp_base_url': "https://smp-demo.nemhandel.dk",
                    'ttl': 60,
                    'service_group_url': f'http:///smp-demo.nemhandel.dk/iso6523-actorid-upis%3A%3A{url_quoted_nemhandel_identifier}',
                    'services': [
                        {
                            "href": f"https://smp-demo.nemhandel.dk/iso6523-actorid-upis%3A%3A{url_quoted_nemhandel_identifier}/services/busdox-docid-qns%3A%3Aurn%3Aoasis%3Anames%3Aspecification%3Aubl%3Aschema%3Axsd%3ACreditNote-2%3A%3ACreditNote%23%23OIOUBL-2.1%3A%3A2.1",
                            "document_id": "busdox-docid-qns::urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##OIOUBL-2.1::2.1",
                        },
                    ],
                },
            }
            return response

        url = r.path_url.lower()
        body = json.loads(r.body)
        if url == '/api/nemhandel/1/send_document':
            if not body['params']['documents']:
                raise UserError('No documents were provided')
            proxy_documents, responses = cls._get_mock_data(cls.env.context.get('error'), nr_invoices=len(body['params']['documents']))
        elif url == '/api/nemhandel/1/send_response':
            num_responses = len(body['params']['reference_uuids'])
            proxy_documents, responses = cls._get_mock_data(cls.env.context.get('error'), nr_invoices=num_responses)
        else:
            proxy_documents, responses = cls._get_mock_data(cls.env.context.get('error'))

        if url == '/api/nemhandel/1/get_document':
            uuid = body['params']['message_uuids'][0]
            response.json = lambda: {'result': {uuid: proxy_documents[uuid]}}
            return response

        if url not in responses:
            return super()._request_handler(s, r, **kw)
        response.json = lambda: responses[url]
        return response