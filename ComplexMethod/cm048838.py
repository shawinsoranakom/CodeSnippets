def make_efactura_request(session, company, endpoint, params, data=None) -> dict[str, str | bytes]:
    """
    Make an API request to the Romanian SPV, handle the response, and return a ``result`` dictionary.

    :param session: ``requests`` or ``requests.Session()`` object
    :param company: ``res.company`` object containing l10n_ro_edi_test_env, l10n_ro_edi_access_token
    :param endpoint: ``upload`` (for sending) | ``stareMesaj`` (for fetching status) | ``descarcare`` (for downloading answer) |``listaMesajeFactura`` (to obtain the latest messages from efactura) | ``transformare`` (to get the official PDF from efactura)
    :param params: Dictionary of query parameters
    :param data: XML data for ``upload`` request
    :return: Dictionary of {'error': `str`, ['timeout': True for Timeout errors]} or {'content': <response.content>} from E-Factura
    """
    send_mode = 'test' if company.l10n_ro_edi_test_env else 'prod'
    url = f"https://api.anaf.ro/{send_mode}/FCTEL/rest/{endpoint}"
    if endpoint in ['upload', 'uploadb2c', 'transformare']:
        method = 'POST'
    elif endpoint in ['stareMesaj', 'descarcare', 'listaMesajeFactura']:
        method = 'GET'
    else:
        return {'error': company.env._('Unknown endpoint.')}
    headers = {'Content-Type': 'application/xml',
               'Authorization': f'Bearer {company.l10n_ro_edi_access_token}'}
    if endpoint == 'transformare':
        url = "https://webservicesp.anaf.ro/prod/FCTEL/rest/transformare/FACT1/DA"
        headers = {'Content-Type': 'text/plain'}

    try:
        response = session.request(method=method, url=url, params=params, data=data, headers=headers, timeout=60)
    except requests.HTTPError as e:
        return {'error': e}
    except (requests.ConnectionError, requests.Timeout):
        return {
            'error': company.env._('Timeout while sending to SPV. Use Synchronise to SPV to update the status.'),
            'timeout': True,
        }

    if response.status_code == 204:
        return {'error': company.env._('You reached the limit of requests. Please try again later.')}
    if response.status_code == 400:
        error_json = response.json()
        return {'error': error_json['message']}
    if response.status_code == 401:
        return {'error': company.env._('Access token is unauthorized.')}
    if response.status_code == 403:
        return {'error': company.env._('Access token is forbidden.')}
    if response.status_code == 500:
        return {'error': company.env._('There is something wrong with the SPV. Please try again later.')}

    return {'content': response.content}