def _get_requested_clients(self, url, smuggled_data, is_premium_subscriber):
        requested_clients = []
        excluded_clients = []
        js_runtime_available = any(p.is_available() for p in self._jsc_director.providers.values())
        default_clients = (
            self._DEFAULT_PREMIUM_CLIENTS if is_premium_subscriber
            else self._DEFAULT_AUTHED_CLIENTS if self.is_authenticated
            else self._DEFAULT_JSLESS_CLIENTS if not js_runtime_available
            else self._DEFAULT_CLIENTS
        )
        allowed_clients = sorted(
            (client for client in INNERTUBE_CLIENTS if client[:1] != '_'),
            key=lambda client: INNERTUBE_CLIENTS[client]['priority'], reverse=True)
        for client in self._configuration_arg('player_client'):
            if client == 'default':
                requested_clients.extend(default_clients)
            elif client == 'all':
                requested_clients.extend(allowed_clients)
            elif client.startswith('-'):
                excluded_clients.append(client[1:])
            elif client not in allowed_clients:
                self.report_warning(f'Skipping unsupported client "{client}"')
            else:
                requested_clients.append(client)

        if not (requested_clients or excluded_clients) and default_clients == self._DEFAULT_JSLESS_CLIENTS:
            self.report_warning(
                f'No supported JavaScript runtime could be found. Only deno is enabled by default; '
                f'to use another runtime add  --js-runtimes RUNTIME[:PATH]  to your command/config. '
                f'YouTube extraction without a JS runtime has been deprecated, and some formats may be missing. '
                f'See  {_EJS_WIKI_URL}  for details on installing one', only_once=True)

        if not requested_clients:
            requested_clients.extend(default_clients)
        for excluded_client in excluded_clients:
            if excluded_client in requested_clients:
                requested_clients.remove(excluded_client)
        if not requested_clients:
            raise ExtractorError('No player clients have been requested', expected=True)

        if self.is_authenticated:
            if (smuggled_data.get('is_music_url') or self.is_music_url(url)) and 'web_music' not in requested_clients:
                requested_clients.append('web_music')

            unsupported_clients = [
                client for client in requested_clients if not INNERTUBE_CLIENTS[client]['SUPPORTS_COOKIES']
            ]
            for client in unsupported_clients:
                self.report_warning(f'Skipping client "{client}" since it does not support cookies', only_once=True)
                requested_clients.remove(client)

        return orderedSet(requested_clients)