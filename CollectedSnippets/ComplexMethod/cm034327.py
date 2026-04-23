def _call_galaxy(self, url, args=None, headers=None, method=None, auth_required=False, error_context_msg=None,
                     cache=False, cache_key=None):
        url_info = urlparse(url)
        cache_id = get_cache_id(url)
        if not cache_key:
            cache_key = url_info.path
        query = parse_qs(url_info.query)
        if cache and self._cache:
            server_cache = self._cache.setdefault(cache_id, {})
            iso_datetime_format = '%Y-%m-%dT%H:%M:%SZ'

            valid = False
            if cache_key in server_cache:
                expires = datetime.datetime.strptime(server_cache[cache_key]['expires'], iso_datetime_format)
                expires = expires.replace(tzinfo=datetime.timezone.utc)
                valid = datetime.datetime.now(datetime.timezone.utc) < expires

            is_paginated_url = 'page' in query or 'offset' in query
            if valid and not is_paginated_url:
                # Got a hit on the cache and we aren't getting a paginated response
                path_cache = server_cache[cache_key]
                if path_cache.get('paginated'):
                    if '/v3/' in cache_key:
                        res = {'links': {'next': None}}
                    else:
                        res = {'next': None}

                    # Technically some v3 paginated APIs return in 'data' but the caller checks the keys for this so
                    # always returning the cache under results is fine.
                    res['results'] = []
                    for result in path_cache['results']:
                        res['results'].append(result)

                else:
                    try:
                        res = path_cache['results']
                    except KeyError as cache_miss_error:
                        raise AnsibleError(
                            f"Missing expected 'results' in ansible-galaxy cache: {path_cache!r}. "
                            "This may indicate cache corruption (for example, from concurrent ansible-galaxy runs) "
                            "or a bug in how the cache was generated. "
                            "Try running with --clear-response-cache or --no-cache to work around the issue."
                        ) from cache_miss_error

                return res

            elif not is_paginated_url:
                # The cache entry had expired or does not exist, start a new blank entry to be filled later.
                expires = datetime.datetime.now(datetime.timezone.utc)
                expires += datetime.timedelta(days=1)
                server_cache[cache_key] = {
                    'expires': expires.strftime(iso_datetime_format),
                    'paginated': False,
                }

        headers = headers or {}
        self._add_auth_token(headers, url, required=auth_required)

        try:
            display.vvvv("Calling Galaxy at %s" % url)
            resp = open_url(to_native(url), data=args, validate_certs=self.validate_certs, headers=headers,
                            method=method, timeout=self._server_timeout, http_agent=user_agent(), follow_redirects='safe')
        except HTTPError as e:
            raise GalaxyError(e, error_context_msg)
        except Exception as ex:
            raise AnsibleError(f"Unknown error when attempting to call Galaxy at {url!r}.") from ex

        resp_data = to_text(resp.read(), errors='surrogate_or_strict')
        try:
            data = json.loads(resp_data)
        except ValueError:
            raise AnsibleError("Failed to parse Galaxy response from '%s' as JSON:\n%s"
                               % (resp.url, to_native(resp_data)))

        if cache and self._cache:
            path_cache = self._cache[cache_id][cache_key]

            # v3 can return data or results for paginated results. Scan the result so we can determine what to cache.
            paginated_key = None
            for key in ['data', 'results']:
                if key in data:
                    paginated_key = key
                    break

            if paginated_key:
                path_cache['paginated'] = True
                results = path_cache.setdefault('results', [])
                for result in data[paginated_key]:
                    results.append(result)

            else:
                path_cache['results'] = data

        return data