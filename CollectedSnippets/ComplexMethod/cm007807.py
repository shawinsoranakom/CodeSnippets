def _real_extract(self, url):
        display_id = self._match_id(url).split('/')[-1]

        webpage = self._download_webpage(url, display_id)
        # extraction based on https://github.com/ytdl-org/youtube-dl/issues/29341
        '''
        <div id="video-106908"
            class="simplestream"
            data-id="GB001"
            data-type="vod"
            data-key="3Li3Nt2Qs8Ct3Xq9Fi5Uy0Mb2Bj0Qs"
            data-token="f9c317c727dc07f515b20036c8ef14a6"
            data-expiry="1624300052"
            data-uvid="37900558"
            data-poster="https://thumbnails.simplestreamcdn.com/gbnews/ondemand/37900558.jpg?width=700&"
            data-npaw="false"
            data-env="production">
        '''
        # exception if no match
        video_data = self._search_regex(
            r'(<div\s[^>]*\bclass\s*=\s*(\'|")(?!.*sidebar\b)simplestream(?:\s[\s\w$-]*)?\2[^>]*>)',
            webpage, 'video data')

        video_data = extract_attributes(video_data)
        ss_id = video_data.get('data-id')
        if not ss_id:
            raise ExtractorError('Simplestream ID not found')

        json_data = self._download_json(
            self._SSMP_URL, display_id,
            note='Downloading Simplestream JSON metadata',
            errnote='Unable to download Simplestream JSON metadata',
            query={
                'id': ss_id,
                'env': video_data.get('data-env', 'production'),
            }, fatal=False)

        meta_url = traverse_obj(json_data, ('response', 'api_hostname'))
        if not meta_url:
            raise ExtractorError('No API host found')

        uvid = video_data['data-uvid']
        dtype = video_data.get('data-type')
        stream_data = self._download_json(
            '%s/api/%s/stream/%s' % (meta_url, 'show' if dtype == 'vod' else dtype, uvid),
            uvid,
            query={
                'key': video_data.get('data-key'),
                'platform': self._PLATFORM,
            },
            headers={
                'Token': video_data.get('data-token'),
                'Token-Expiry': video_data.get('data-expiry'),
                'Uvid': uvid,
            }, fatal=False)

        stream_url = traverse_obj(stream_data, (
            'response', 'stream', T(url_or_none)))
        if not stream_url:
            raise ExtractorError('No stream data/URL')

        # now known to be a dict
        stream_data = stream_data['response']
        drm = stream_data.get('drm')
        if drm:
            self.report_drm(uvid)

        formats = self._extract_m3u8_formats(
            stream_url, uvid, ext='mp4', entry_protocol='m3u8_native',
            fatal=False)
        # exception if no formats
        self._sort_formats(formats)

        return {
            'id': uvid,
            'display_id': display_id,
            'title': (traverse_obj(stream_data, ('title', T(txt_or_none)))
                      or self._og_search_title(webpage, default=None)
                      or display_id.replace('-', ' ').capitalize()),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': (traverse_obj(video_data, ('data-poster', T(url_or_none)))
                          or self._og_search_thumbnail(webpage)),
            'formats': formats,
            'is_live': (dtype == 'live') or None,
        }