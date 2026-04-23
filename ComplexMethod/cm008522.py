def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        params = extract_attributes(self._search_regex(
            r'(?s)(<[^>]+id="video"[^>]*>)', webpage, 'params'))
        variants = self._parse_json(
            try_get(params, lambda x: x['data-video-variants'], str) or '{}',
            video_id, fatal=False)
        # Prefer last matching featureset
        # See: https://github.com/yt-dlp/yt-dlp/issues/986
        platform_tag_video, featureset_video = next(
            ((platform_tag, featureset)
             for platform_tag, featuresets in reversed(list(variants.items())) for featureset in featuresets
             if set(try_get(featureset, lambda x: x[:2]) or []) == {'aes', 'hls'}),
            (None, None))
        if not platform_tag_video or not featureset_video:
            raise ExtractorError('No downloads available', expected=True, video_id=video_id)

        ios_playlist_url = params.get('data-video-playlist') or params['data-video-id']
        headers = self._generate_api_headers(params['data-video-hmac'])
        ios_playlist = self._call_api(
            video_id, ios_playlist_url, headers, platform_tag_video, featureset_video)

        video_data = try_get(ios_playlist, lambda x: x['Playlist']['Video'], dict) or {}
        ios_base_url = video_data.get('Base')
        formats = []
        for media_file in (video_data.get('MediaFiles') or []):
            href = media_file.get('Href')
            if not href:
                continue
            if ios_base_url:
                href = ios_base_url + href
            ext = determine_ext(href)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    href, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'url': href,
                })
        info = self._search_json_ld(webpage, video_id, default={})
        if not info:
            json_ld = self._parse_json(self._search_regex(
                JSON_LD_RE, webpage, 'JSON-LD', '{}',
                group='json_ld'), video_id, fatal=False)
            if json_ld and json_ld.get('@type') == 'BreadcrumbList':
                for ile in (json_ld.get('itemListElement:') or []):
                    item = ile.get('item:') or {}
                    if item.get('@type') == 'TVEpisode':
                        item['@context'] = 'http://schema.org'
                        info = self._json_ld(item, video_id, fatal=False) or {}
                        break

        thumbnails = []
        thumbnail_url = try_get(params, lambda x: x['data-video-posterframe'], str)
        if thumbnail_url:
            thumbnails.extend([{
                'url': thumbnail_url.format(width=1920, height=1080, quality=100, blur=0, bg='false'),
                'width': 1920,
                'height': 1080,
            }, {
                'url': urljoin(base_url(thumbnail_url), url_basename(thumbnail_url)),
                'preference': -2,
            }])

        thumbnail_url = self._html_search_meta(['og:image', 'twitter:image'], webpage, default=None)
        if thumbnail_url:
            thumbnails.append({
                'url': thumbnail_url,
            })
        self._remove_duplicate_formats(thumbnails)

        return merge_dicts({
            'id': video_id,
            'title': self._html_search_meta(['og:title', 'twitter:title'], webpage),
            'formats': formats,
            'subtitles': self.extract_subtitles(video_id, variants, ios_playlist_url, headers),
            'duration': parse_duration(video_data.get('Duration')),
            'description': clean_html(get_element_by_class('episode-info__synopsis', webpage)),
            'thumbnails': thumbnails,
        }, info)