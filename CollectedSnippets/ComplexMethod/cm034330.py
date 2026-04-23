def get_collection_versions(self, namespace, name):
        """
        Gets a list of available versions for a collection on a Galaxy server.

        :param namespace: The collection namespace.
        :param name: The collection name.
        :return: A list of versions that are available.
        """
        api_path = self.available_api_versions['v3']
        pagination_path = ['links', 'next']

        versions_url = _urljoin(self.api_server, api_path, 'collections', namespace, name, 'versions', '/?limit=%d' % COLLECTION_PAGE_SIZE)
        versions_url_info = urlparse(versions_url)
        cache_key = versions_url_info.path

        # We should only rely on the cache if the collection has not changed. This may slow things down but it ensures
        # we are not waiting a day before finding any new collections that have been published.
        if self._cache:
            server_cache = self._cache.setdefault(get_cache_id(versions_url), {})
            modified_cache = server_cache.setdefault('modified', {})

            try:
                modified_date = self.get_collection_metadata(namespace, name).modified_str
            except GalaxyError as err:
                if err.http_code != 404:
                    raise
                # No collection found, return an empty list to keep things consistent with the various APIs
                return []

            cached_modified_date = modified_cache.get('%s.%s' % (namespace, name), None)
            if cached_modified_date != modified_date:
                modified_cache['%s.%s' % (namespace, name)] = modified_date
                if versions_url_info.path in server_cache:
                    del server_cache[cache_key]

                self._set_cache()

        error_context_msg = 'Error when getting available collection versions for %s.%s from %s (%s)' \
                            % (namespace, name, self.name, self.api_server)

        try:
            data = self._call_galaxy(versions_url, error_context_msg=error_context_msg, cache=True, cache_key=cache_key)
        except GalaxyError as err:
            if err.http_code != 404:
                raise
            # v3 doesn't raise a 404 so we need to mimic the empty response from APIs that do.
            return []

        if 'data' in data:
            # v3 automation-hub is the only known API that uses `data`
            # since v3 pulp_ansible does not, we cannot rely on version
            # to indicate which key to use
            results_key = 'data'
        else:
            results_key = 'results'

        versions = []
        while True:
            for v in data[results_key]:
                versions.append(v["version"])
                # requires_ansible is new in galaxy_ng 4.3.0
                self.requires_ansible[f"{namespace}.{name}"][v["version"]] = v.get("requires_ansible")

            next_link = data
            for path in pagination_path:
                next_link = next_link.get(path, {})

            if not next_link:
                break
            next_link_info = urlparse(next_link)
            if not next_link_info.scheme and not next_link_info.path.startswith('/'):
                raise AnsibleError(f'Invalid non absolute pagination link: {next_link}')
            next_link = urljoin(self.api_server, next_link)

            data = self._call_galaxy(to_native(next_link, errors='surrogate_or_strict'),
                                     error_context_msg=error_context_msg, cache=True, cache_key=cache_key)
        self._set_cache()

        return versions