def mock_requests_request(method, url, *args, **kwargs):
    response = MagicMock()
    response.status_code = 200

    if method == 'GET' and 'Check/TaxNumber' in url:
        if EINVOICE_PARTNER_VAT in url:
            response.json.return_value = [
                {
                    'DocumentType': 'Invoice',
                    'Name': 'urn:mail:salt@bae.com',
                    'TaxNumber': EINVOICE_PARTNER_VAT,
                    'Title': 'Salt Bae LLC',
                    'Type': 'OZEL',
                },
            ]
        elif COMPANY_VAT in url:
            response.json.return_value = [
                {
                    'TaxNumber': 'text',
                    'Title': 'text',
                    'FirstCreatedTime': '2025-06-23',
                    'CreationTime': '2025-06-23',
                    'DocumentType': 'text',
                    'Name': 'text',
                    'Type': 'text',
                },
            ]
        elif EARCHIVE_PARTNER_VAT in url:
            response.json.return_value = []

    elif method == 'GET' and (match := re.fullmatch(r'/einvoice/sale/([\w-]+)/Status', url)):
        if match.group(1) == UUID_INVALID_STATUS:
            data = {
                "InvoiceStatus": {
                    "Code": "boop",
                    "Description": "text",
                    "DetailDescription": "text",
                },
            }
            response.get.side_effect = data.get
        else:
            data = {
                "InvoiceStatus": {
                    "Code": "succeed",
                    "Description": "text",
                    "DetailDescription": "text",
                },
            }
            response.get.side_effect = data.get

    elif method == 'POST' and 'Send/Xml' in url:
        if UNAUTHORIZED_ALIAS in url:
            response.status_code = 401
            response.text = 'Unauthorized'
        elif SERVER_ERROR_ALIAS in url:
            response.status_code = 500
            response.text = 'Internal Server Error'
        elif ERRORENOUS_ALIAS in url:
            response.status_code = 422
            response.json.return_value = {
                "Message": "HATALI ISTEK",
                "Errors": [{
                    "Code": 2000,
                    "Description": "Yeterli Kontörünüz Bulunmamaktadır.",
                    "Detail": "Yeterli Kontörünüz Bulunmamaktadır. Lütfen Kontör Alımı Yapınız.",
                }],
            }
        else:
            response.json.return_value = {
                "UUID": "00aac88a-576b-4a62-98b5-ed34fe4d187d",
                "InvoiceNumber": "",
            }

    elif method == 'GET' and '/einvoice/Purchase' in url:
        if '/xml' in url:
            with file_open('l10n_tr_nilvera_einvoice/tests/test_files/fetching/invoice.xml', 'rb') as xml:
                response = xml.read()
        elif '/pdf' in url:
            with file_open('l10n_tr_nilvera_einvoice/tests/test_files/fetching/invoice.pdf', 'rb') as pdf:
                response = pdf.read()
        else:
            data = {
                    'TotalPages': 1,
                    'Content': [
                        {
                            'UUID': 'invoice_uuid',
                            'CreatedDate': '2026-02-02',
                        },
                    ],
            }
            response.get.side_effect = data.get
    return response