def _do_request(self, uri, params=None, headers=None, method='POST', preuri=DEFAULT_MICROSOFT_GRAPH_ENDPOINT, timeout=TIMEOUT):
        """ Execute the request to Microsoft API. Return a tuple ('HTTP_CODE', 'HTTP_RESPONSE')
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
            urls.url_parse(url).host for url in (DEFAULT_MICROSOFT_TOKEN_ENDPOINT, DEFAULT_MICROSOFT_GRAPH_ENDPOINT)
        ]

        _logger.debug("Uri: %s - Type : %s - Headers: %s - Params : %s !" % (uri, method, headers, params))

        ask_time = fields.Datetime.now()
        try:
            if method.upper() in ('GET', 'DELETE'):
                res = requests.request(method.lower(), preuri + uri, headers=headers, params=params, timeout=timeout)
            elif method.upper() in ('POST', 'PATCH', 'PUT'):
                res = requests.request(method.lower(), preuri + uri, data=params, headers=headers, timeout=timeout)
            else:
                raise Exception(_('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!', method))
            res.raise_for_status()
            status = res.status_code

            if int(status) in RESOURCE_NOT_FOUND_STATUSES:
                response = {}
            else:
                # Some answers return empty content
                response = res.content and res.json() or {}

            try:
                ask_time = datetime.strptime(res.headers.get('date'), "%a, %d %b %Y %H:%M:%S %Z")
            except:
                pass
        except requests.HTTPError as error:
            if error.response.status_code in RESOURCE_NOT_FOUND_STATUSES:
                status = error.response.status_code
                response = {}
            else:
                _logger.exception("Bad microsoft request: %s!", error.response.content)
                raise error
        return (status, response, ask_time)