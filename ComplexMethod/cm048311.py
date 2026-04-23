def _do_request(self, uri, params=None, headers=None, method='POST', preuri=GOOGLE_API_BASE_URL, timeout=TIMEOUT):
        """ Execute the request to Google API. Return a tuple ('HTTP_CODE', 'HTTP_RESPONSE')
            :param uri : the url to contact
            :param params : dict or already encoded parameters for the request to make
            :param headers : headers of request
            :param method : the method to use to make the request
            :param preuri : pre url to prepend to param uri.
        """
        if params is None:
            params = {}
        if headers is None:
            headers = {}

        assert urls.url_parse(preuri + uri).host in [
            urls.url_parse(url).host for url in (GOOGLE_TOKEN_ENDPOINT, GOOGLE_API_BASE_URL)
        ]

        # Remove client_secret key from logs
        if isinstance(params, str):
            _log_params = json.loads(params) or {}
        else:
            _log_params = (params or {}).copy()
        if _log_params.get('client_secret'):
            _log_params['client_secret'] = str(_log_params['client_secret'])[0:4] + 'x' * 12

        _logger.debug("Uri: %s - Type : %s - Headers: %s - Params : %s!", uri, method, headers, _log_params)

        ask_time = fields.Datetime.now()
        try:
            if method.upper() in ('GET', 'DELETE'):
                res = requests.request(method.lower(), preuri + uri, params=params, timeout=timeout)
            elif method.upper() in ('POST', 'PATCH', 'PUT'):
                res = requests.request(method.lower(), preuri + uri, data=params, headers=headers, timeout=timeout)
            else:
                raise Exception(_('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!', method))
            res.raise_for_status()
            status = res.status_code

            if int(status) == 204:  # Page not found, no response
                response = False
            else:
                response = res.json()

            try:
                ask_time = datetime.strptime(res.headers.get('date', ''), "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                pass
        except requests.HTTPError as error:
            if error.response.status_code in (204, 404):
                status = error.response.status_code
                response = ""
            else:
                _logger.exception("Bad google request : %s!", error.response.content)
                raise error
        return (status, response, ask_time)