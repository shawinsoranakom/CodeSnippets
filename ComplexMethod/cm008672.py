def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        self._initialize_geo_bypass({
            'countries': smuggled_data.get('geo_countries'),
            'ip_blocks': smuggled_data.get('geo_ip_blocks'),
        })

        account_id, player_id, embed, content_type, video_id = self._match_valid_url(url).groups()

        policy_key_id = f'{account_id}_{player_id}'
        policy_key = self.cache.load('brightcove', policy_key_id)
        policy_key_extracted = False
        store_pk = lambda x: self.cache.store('brightcove', policy_key_id, x)

        def extract_policy_key():
            base_url = f'https://players.brightcove.net/{account_id}/{player_id}_{embed}/'
            config = self._download_json(
                base_url + 'config.json', video_id, fatal=False) or {}
            policy_key = try_get(
                config, lambda x: x['video_cloud']['policy_key'])
            if not policy_key:
                webpage = self._download_webpage(
                    base_url + 'index.min.js', video_id)

                catalog = self._search_regex(
                    r'catalog\(({.+?})\);', webpage, 'catalog', default=None)
                if catalog:
                    catalog = self._parse_json(
                        js_to_json(catalog), video_id, fatal=False)
                    if catalog:
                        policy_key = catalog.get('policyKey')

                if not policy_key:
                    policy_key = self._search_regex(
                        r'policyKey\s*:\s*(["\'])(?P<pk>.+?)\1',
                        webpage, 'policy key', group='pk')

            store_pk(policy_key)
            return policy_key

        token = smuggled_data.get('token')
        api_url = f'https://{"edge-auth" if token else "edge"}.api.brightcove.com/playback/v1/accounts/{account_id}/{content_type}s/{video_id}'
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        referrer = smuggled_data.get('referrer')  # XXX: notice the spelling/case of the key
        if referrer:
            headers.update({
                'Referer': referrer,
                'Origin': re.search(r'https?://[^/]+', referrer).group(0),
            })

        for _ in range(2):
            if not policy_key:
                policy_key = extract_policy_key()
                policy_key_extracted = True
            headers['Accept'] = f'application/json;pk={policy_key}'
            try:
                json_data = self._download_json(api_url, video_id, headers=headers)
                break
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status in (401, 403):
                    json_data = self._parse_json(e.cause.response.read().decode(), video_id)[0]
                    message = json_data.get('message') or json_data['error_code']
                    if json_data.get('error_subcode') == 'CLIENT_GEO':
                        self.raise_geo_restricted(msg=message)
                    elif json_data.get('error_code') == 'INVALID_POLICY_KEY' and not policy_key_extracted:
                        policy_key = None
                        store_pk(None)
                        continue
                    raise ExtractorError(message, expected=True)
                raise

        errors = json_data.get('errors')
        if errors and errors[0].get('error_subcode') == 'TVE_AUTH':
            custom_fields = json_data['custom_fields']
            missing_fields = ', '.join(
                key for key in ('source_url', 'software_statement') if not smuggled_data.get(key))
            if missing_fields:
                raise ExtractorError(
                    f'Missing fields in smuggled data: {missing_fields}. '
                    f'This video can be only extracted from the webpage where it is embedded. '
                    f'Pass the URL of the embedding webpage instead of the Brightcove URL', expected=True)
            tve_token = self._extract_mvpd_auth(
                smuggled_data['source_url'], video_id,
                custom_fields['bcadobepassrequestorid'],
                custom_fields['bcadobepassresourceid'],
                smuggled_data['software_statement'])
            json_data = self._download_json(
                api_url, video_id, headers={
                    'Accept': f'application/json;pk={policy_key}',
                }, query={
                    'tveToken': tve_token,
                })

        if content_type == 'playlist':
            return self.playlist_result(
                (self._parse_brightcove_metadata(vid, vid['id'], headers)
                 for vid in traverse_obj(json_data, ('videos', lambda _, v: v['id']))),
                json_data.get('id'), json_data.get('name'),
                json_data.get('description'))

        return self._parse_brightcove_metadata(
            json_data, video_id, headers=headers)