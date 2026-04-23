def _real_extract(self, url):
        video_id, type_ = self._match_valid_url(url).group('id', 'type')
        is_live = type_ == 'live'

        webpage = self._download_webpage(url, video_id)
        if 'Streaming is not available in your area' in webpage:
            self.raise_geo_restricted()

        media_url = (
            self._search_regex(
                r'var\s+streamURL\s*=\s*[\'"]([^?\'"]+)', webpage, 'stream url', default=None)
            # Source URL must be used only if streamURL is unavailable
            or self._search_regex(
                r'<source[^>]+src=[\'"]([^\'"]+)', webpage, 'source url', default=None))
        if not media_url:
            youtube_url = self._search_regex(r'file:\s*[\'"]((?:https?:)//(?:www\.)?youtube\.com[^\'"]+)',
                                             webpage, 'youtube url', default=None)
            if youtube_url:
                return self.url_result(youtube_url, 'Youtube')
            raise ExtractorError('Unable to extract stream url')

        token_array = self._search_json(
            r'<script>var\s+_\$_[a-zA-Z0-9]+\s*=', webpage, 'access token array', video_id,
            contains_pattern=r'\[(?s:.+)\]', default=None, transform_source=js_to_json)
        if token_array:
            token_url = traverse_obj(token_array, (..., {url_or_none}), get_all=False)
            if not token_url:
                raise ExtractorError('Invalid access token array')
            access_token = self._download_json(
                token_url, video_id, note='Downloading access token')['data']['authToken']
            media_url = update_url_query(media_url, {'auth-token': access_token})

        ext = determine_ext(media_url)
        if ext == 'm3u8':
            formats = self._extract_m3u8_formats(media_url, video_id, live=is_live)
        elif ext == 'mp3':
            formats = [{
                'url': media_url,
                'vcodec': 'none',
            }]
        else:
            formats = [{'url': media_url}]

        return {
            'id': video_id,
            'title': (self._search_regex(r'var\s+titleVideo\s*=\s*[\'"]([^\'"]+)',
                                         webpage, 'title', default=None)
                      or self._og_search_title(webpage)),
            'creator': self._search_regex(r'var\s+videoAuthor\s*=\s*[\'"]([^?\'"]+)',
                                          webpage, 'videoAuthor', default=None),
            'thumbnail': (self._search_regex(r'var\s+posterIMG\s*=\s*[\'"]([^?\'"]+)',
                                             webpage, 'thumbnail', default=None)
                          or self._og_search_thumbnail(webpage)),
            'formats': formats,
            'is_live': is_live,
        }