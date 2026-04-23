def _process_ooyala_element(self, webpage, sdc_el, url):
        sdc = extract_attributes(sdc_el)
        provider = sdc.get('data-provider')
        if provider == 'ooyala':
            video_id = sdc['data-sdc-video-id']
            video_url = 'ooyala:%s' % video_id
            ie_key = 'Ooyala'
            ooyala_el = self._search_regex(
                r'(<div[^>]+class="[^"]*\bsdc-article-video__media-ooyala\b[^"]*"[^>]+data-video-id="%s"[^>]*>)' % video_id,
                webpage, 'video data', fatal=False)
            if ooyala_el:
                ooyala_attrs = extract_attributes(ooyala_el) or {}
                if ooyala_attrs.get('data-token-required') == 'true':
                    token_fetch_url = (self._parse_json(ooyala_attrs.get(
                        'data-token-fetch-options', '{}'),
                        video_id, fatal=False) or {}).get('url')
                    if token_fetch_url:
                        embed_token = self._download_json(urljoin(
                            url, token_fetch_url), video_id, fatal=False)
                        if embed_token:
                            video_url = smuggle_url(
                                video_url, {'embed_token': embed_token})
        elif provider == 'brightcove':
            video_id = sdc['data-video-id']
            account_id = sdc.get('data-account-id') or '6058004172001'
            player_id = sdc.get('data-player-id') or 'RC9PQUaJ6'
            video_url = self.BRIGHTCOVE_URL_TEMPLATE % (account_id, player_id, video_id)
            ie_key = 'BrightcoveNew'

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': video_url,
            'ie_key': ie_key,
        }