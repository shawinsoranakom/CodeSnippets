def _extract_graphql(self, data, url):
        # Parses GraphQL queries containing videos and generates a playlist.
        uploader_id = self._match_id(url)
        csrf_token = data['config']['csrf_token']
        rhx_gis = data.get('rhx_gis') or '3c7ca9dcefcf966d11dacf1f151335e8'

        cursor = ''
        for page_num in itertools.count(1):
            variables = {
                'first': 12,
                'after': cursor,
            }
            variables.update(self._query_vars_for(data))
            variables = json.dumps(variables)

            if self._gis_tmpl:
                gis_tmpls = [self._gis_tmpl]
            else:
                gis_tmpls = [
                    f'{rhx_gis}',
                    '',
                    f'{rhx_gis}:{csrf_token}',
                    '{}:{}:{}'.format(rhx_gis, csrf_token, self.get_param('http_headers')['User-Agent']),
                ]

            # try all of the ways to generate a GIS query, and not only use the
            # first one that works, but cache it for future requests
            for gis_tmpl in gis_tmpls:
                try:
                    json_data = self._download_json(
                        'https://www.instagram.com/graphql/query/', uploader_id,
                        f'Downloading JSON page {page_num}', headers={
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-Instagram-GIS': hashlib.md5(
                                (f'{gis_tmpl}:{variables}').encode()).hexdigest(),
                        }, query={
                            'query_hash': self._QUERY_HASH,
                            'variables': variables,
                        })
                    media = self._parse_timeline_from(json_data)
                    self._gis_tmpl = gis_tmpl
                    break
                except ExtractorError as e:
                    # if it's an error caused by a bad query, and there are
                    # more GIS templates to try, ignore it and keep trying
                    if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                        if gis_tmpl != gis_tmpls[-1]:
                            continue
                    raise

            nodes = traverse_obj(media, ('edges', ..., 'node'), expected_type=dict) or []
            if not nodes:
                break
            yield from self._extract_nodes(nodes)

            has_next_page = traverse_obj(media, ('page_info', 'has_next_page'))
            cursor = traverse_obj(media, ('page_info', 'end_cursor'), expected_type=str)
            if not has_next_page or not cursor:
                break