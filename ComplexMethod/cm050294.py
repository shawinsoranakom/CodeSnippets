def _l10n_eg_eta_connect_to_server(self, request_data, request_url, method, is_access_token_req=False, production_enviroment=False):
        api_domain = is_access_token_req and self._l10n_eg_get_eta_token_domain(production_enviroment) or self._l10n_eg_get_eta_api_domain(production_enviroment)
        request_url = api_domain + request_url
        try:
            session = requests.session()
            session.mount("https://", LegacyHTTPAdapter())
            request_response = session.request(method, request_url, data=request_data.get('body'), headers=request_data.get('header'), timeout=(5, 10))
        except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema, requests.exceptions.Timeout, requests.exceptions.HTTPError) as ex:
            return {
                'error': str(ex),
                'blocking_level': 'warning'
            }
        if not request_response.ok:
            try:
                response_data = request_response.json()
            except JSONDecodeError as ex:
                return {
                    'error': str(ex),
                    'blocking_level': 'error'
                }
            if response_data and response_data.get('error'):
                return {
                    'error': response_data.get('error'),
                    'blocking_level': 'error'
                }

        try:
            response_data = request_response.json()
        except requests.exceptions.JSONDecodeError:
            response_data = {}

        return {
            'response': str(request_response),
            'ok': request_response.ok,
            'content': request_response.content,
            'data': response_data,
        }