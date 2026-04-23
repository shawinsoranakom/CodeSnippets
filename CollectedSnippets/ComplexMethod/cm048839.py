def _request_ciusro_download_answer(company, key_download, session):
    """
    This method makes a "Download Answer" (GET/descarcare) request to the Romanian SPV. It then processes the
    response by opening the received zip file and returns a dictionary containing:

    - the original invoice and/or the failing response from a bad request / unaccepted XML answer from the SPV
    - the necessary signature information to be stored from the SPV

    :param company: ``res.company`` object
    :param key_download: Content of `key_download` received from `_request_ciusro_send_invoice`
    :param session: ``requests.Session()`` object
    :return: - {'error': ``str``} if there has been an error during the request or parsing of the data
        - {
            'signature': {
                'attachment_raw': ``str``,
                'key_signature': ``str``,
                'key_certificate': ``str``,
            },
            'invoice': {
                'error': ``str``,
            } -> When the invoice is refused
            | {
                'name': ``str``,
                'amount_total': ``float``,
                'due_date': ``datetime``,
                'attachment_raw': ``str``,
            } -> When the invoice is accepted
        }
    """
    result = make_efactura_request(
        session=session,
        company=company,
        endpoint='descarcare',
        params={'id': key_download},
    )
    if 'error' in result:
        return result

    # E-Factura gives download response in ZIP format
    try:
        # The ZIP will contain two files,
        # one with the electronic signature (containing 'semnatura' in the filename),
        # and the other with one with the original invoice, the requested invoice or the identified errors.
        extracted_data = {'signature': {}, 'invoice': {}}
        with zipfile.ZipFile(io.BytesIO(result['content'])) as zip_ref:
            for file in zip_ref.infolist():
                file_bytes = zip_ref.read(file)
                root = etree.fromstring(file_bytes)

                # Extract the signature
                if 'semnatura' in file.filename:
                    attachment_raw = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
                    extracted_data['signature'] = {
                        'attachment_raw': attachment_raw,
                        'key_signature': root.findtext('.//ns:SignatureValue', namespaces=NS_SIGNATURE),
                        'key_certificate': root.findtext('.//ns:X509Certificate', namespaces=NS_SIGNATURE),
                    }

                # Extract the invoice or the errors if there are any
                else:
                    if error_elements := root.findall('.//ns:Error', namespaces=NS_HEADER):
                        extracted_data['invoice']['error'] = ('\n\n').join(error.get('errorMessage') for error in error_elements)

                    else:
                        extracted_data['invoice'] = {
                            'name': root.findtext('.//cbc:ID', namespaces=NS_DOWNLOAD),
                            'amount_total': root.findtext('.//cbc:TaxInclusiveAmount', namespaces=NS_DOWNLOAD),
                            'buyer_vat': root.findtext('.//cac:AccountingSupplierParty//cbc:CompanyID', namespaces=NS_DOWNLOAD),
                            'seller_vat': root.findtext('.//cac:AccountingCustomerParty//cbc:CompanyID', namespaces=NS_DOWNLOAD),
                            'date': datetime.strptime(root.findtext('.//cbc:IssueDate', namespaces=NS_DOWNLOAD), '%Y-%m-%d').date(),
                            'attachment_raw': file_bytes,
                        }
        return extracted_data

    except zipfile.BadZipFile:
        try:
            msg_content = json.loads(result['content'].decode())
        except ValueError:
            return {'error': company.env._("The SPV data could not be parsed.")}

        if eroare := msg_content.get('eroare'):
            return {'error': eroare}

    return {'error': company.env._("The SPV data could not be parsed.")}