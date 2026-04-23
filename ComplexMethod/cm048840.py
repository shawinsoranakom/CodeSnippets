def _request_ciusro_synchronize_invoices(company, session, nb_days=1):
    """
    This method makes a "Fetch Messages" (GET/listaMesajeFactura) request to the Romanian SPV.
    After processing the response, if messages were indeed fetched, it will fetch the content
    of said messages.

    Possible returns:
    - {'error': `str`} if there was a failing response from a bad request;
    - {'sent_invoices_messages': [`dict`], 'sent_invoices_refused_messages': [`dict`], 'received_bills_messages': [`dict`]}
    where `dict` is {
        'data_creare': `str`,
        'cif': `str`,
        'id_solicitare': `str`,
        'detalii': `str`,
        'tip': 'FACTURA TRIMISA'|'ERORI FACTURA'|'FACTURA PRIMITA',
        'id': `str`,
        'answer': <`_request_ciusro_download_answer`>
    } representing a message.
    sent_invoices_messages will contain all message validating an invoice, sent_invoices_refused_messages will contain all messages refusing an invoice
    and received_bills_messages will contain all message representing received bills.

    :param company: ``res.company`` object
    :param session: ``requests.Session()`` object
    :param nb_days(optional,default=1): ``int`` the number of days for which the request should be made, min=1, max=60
    :return: {'error': `str`} | {'sent_invoices_messages': [`dict`], 'sent_invoices_refused_messages': [`dict`], 'received_bills_messages': [`dict`]}
    """
    result = make_efactura_request(
        session=session,
        company=company,
        endpoint='listaMesajeFactura',
        params={'zile': nb_days, 'cif': company.vat.replace('RO', '')},
    )
    if 'error' in result:
        return {'error': result['error']}

    try:
        msg_content = json.loads(result['content'])
    except ValueError:
        return {'error': company.env._("The SPV data could not be parsed.")}

    if eroare := msg_content.get('eroare'):
        return {'error': eroare}

    received_bills_messages = []
    sent_invoices_accepted_messages = []
    sent_invoices_refused_messages = []
    for message in msg_content.get('mesaje'):
        message['answer'] = _request_ciusro_download_answer(
            key_download=message['id'],
            company=company,
            session=session,
        )
        if message['tip'] == 'FACTURA TRIMISA':
            sent_invoices_accepted_messages.append(message)
        elif message['tip'] == 'ERORI FACTURA':
            sent_invoices_refused_messages.append(message)
        elif message['tip'] == 'FACTURA PRIMITA':
            received_bills_messages.append(message)

    return {
        'sent_invoices_accepted_messages': sent_invoices_accepted_messages,
        'sent_invoices_refused_messages': sent_invoices_refused_messages,
        'received_bills_messages': received_bills_messages
    }