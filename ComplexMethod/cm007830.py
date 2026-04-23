def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        self._initialize_geo_bypass({
            'countries': smuggled_data.get('geo_countries'),
            'ip_blocks': smuggled_data.get('geo_ip_blocks'),
        })

        account_id, player_id, embed, content_type, video_id = re.match(self._VALID_URL, url).groups()

        policy_key_id = '%s_%s' % (account_id, player_id)
        policy_key = self._downloader.cache.load('brightcove', policy_key_id)
        policy_key_extracted = False
        store_pk = lambda x: self._downloader.cache.store('brightcove', policy_key_id, x)

        def extract_policy_key():
            base_url = 'http://players.brightcove.net/%s/%s_%s/' % (account_id, player_id, embed)
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

        api_url = 'https://edge.api.brightcove.com/playback/v1/accounts/%s/%ss/%s' % (account_id, content_type, video_id)
        headers = {}
        referrer = smuggled_data.get('referrer')
        if referrer:
            headers.update({
                'Referer': referrer,
                'Origin': re.search(r'https?://[^/]+', referrer).group(0),
            })

        for _ in range(2):
            if not policy_key:
                policy_key = extract_policy_key()
                policy_key_extracted = True
            headers['Accept'] = 'application/json;pk=%s' % policy_key
            try:
                json_data = self._download_json(api_url, video_id, headers=headers)
                break
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code in (401, 403):
                    json_data = self._parse_json(e.cause.read().decode(), video_id)[0]
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
            tve_token = self._extract_mvpd_auth(
                smuggled_data['source_url'], video_id,
                custom_fields['bcadobepassrequestorid'],
                custom_fields['bcadobepassresourceid'])
            json_data = self._download_json(
                api_url, video_id, headers={
                    'Accept': 'application/json;pk=%s' % policy_key
                }, query={
                    'tveToken': tve_token,
                })

        if content_type == 'playlist':
            return self.playlist_result(
                [self._parse_brightcove_metadata(vid, vid.get('id'), headers)
                 for vid in json_data.get('videos', []) if vid.get('id')],
                json_data.get('id'), json_data.get('name'),
                json_data.get('description'))

        return self._parse_brightcove_metadata(
            json_data, video_id, headers=headers)