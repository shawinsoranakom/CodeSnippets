def _make_request(company, endpoint_type, params=False):
    """
    Returns:
        For multiple document endpoints (such as query*): list of dicts
        For single document endpoints (such as markPaid): dict
        For receive specifically: bytestring
    """
    endpoints = {
        'send': '/apis/v2/send',
        'query_inbox': '/apis/v2/queryInbox',
        'receive': '/apis/v2/receive',
        'update_status': '/apis/v2/UpdateDokumentProcessStatus',
        'query_status_inbox': '/apis/v2/queryDocumentProcessStatusInbox',
        'query_status_outbox': '/apis/v2/queryDocumentProcessStatusOutbox',
        'notify_import': False,  # Includes eID and has to be handled separately
        'mark_paid': '/api/fiscalization/markPaid',
        'reject': '/api/fiscalization/reject',
        'fisc_outbox': '/api/fiscalization/statusOutbox',
        'fisc_inbox': '/api/fiscalization/statusInbox',
    }
    endpoint = f"/apis/v2/notifyimport/{params.pop('eid')}" if endpoint_type == 'notify_import' else endpoints.get(endpoint_type)
    if not endpoint:
        raise MojEracunServiceError('Invalid API endpoint')
    payload = params
    url = f"{_get_server_url(company)}{endpoint}"

    # Last barrier : in case the demo mode is not handled by the caller, we block access.
    if company.l10n_hr_mer_connection_mode == 'demo':
        raise MojEracunServiceError("block_demo_mode", "Can't access the proxy in demo mode")

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=TIMEOUT,
            headers={'content-type': 'application/json', 'charset': 'utf-8'}
        )
    except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        raise MojEracunServiceError('connection_error',
            company.env._('The url that this service requested returned an error. The url it tried to contact was %s', url))

    # Structure-specific error handling
    if response.status_code != 200:
        try:
            error_message = response.json()
            error_message = error_message.get('errors') or error_message.get('message')
        except (JSONDecodeError, TypeError):
            error_message = False
        raise UserError(company.env._("Error handling request: %s", error_message) if error_message else company.env._("HTTP %s: Connection error.", response.status_code))

    if endpoint != endpoints['receive']:
        try:
            response_json = response.json()
        except (JSONDecodeError, TypeError):
            raise MojEracunServiceError('Invalid response format received')
        if 'error' in response_json:
            message = company.env._('The url that this service requested returned an error. The url it tried to contact was %(url)s. %(error_message)s', url=url, error_message=response_json['error']['message'])
            if response_json['error']['code'] == 404:
                message = company.env._('The url that this service tried to contact does not exist. The url was “%s”', url)
            raise MojEracunServiceError('connection_error', message)
        elif 'Username' in response_json:  # No valid response contains this, it is a credentials error format
            message = company.env._("MER service returned an error: Username '%(name)s': %(desc)s", name=response_json['Username'].get('Value'), desc=response_json['Username'].get('Messages'))
            raise MojEracunServiceError('credentials_error', message)
        return response_json
    else:
        return response.content