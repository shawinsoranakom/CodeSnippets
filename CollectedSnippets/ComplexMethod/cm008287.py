def _real_extract(self, url):
        base_url, temp_id = self._match_valid_url(url).groups()
        webpage = self._download_webpage(url, temp_id)

        video_id = self._search_regex(r"_icareus\['itemId'\]\s*=\s*'(\d+)'", webpage, 'video_id')
        organization_id = self._search_regex(r"_icareus\['organizationId'\]\s*=\s*'(\d+)'", webpage, 'organization_id')

        assets = self._download_json(
            self._search_regex(r'var\s+publishingServiceURL\s*=\s*"(http[^"]+)";', webpage, 'api_base'),
            video_id, data=urlencode_postdata({
                'version': '03',
                'action': 'getAssetPlaybackUrls',
                'organizationId': organization_id,
                'assetId': video_id,
                'token': self._search_regex(r"_icareus\['token'\]\s*=\s*'([a-f0-9]+)'", webpage, 'icareus_token'),
            }))

        subtitles = {
            remove_end(sdesc.split(' ')[0], ':'): [{'url': url_or_none(surl)}]
            for _, sdesc, surl in assets.get('subtitles') or []
        }

        formats = [{
            'format': item.get('name'),
            'format_id': 'audio',
            'vcodec': 'none',
            'url': url_or_none(item['url']),
            'tbr': int_or_none(self._search_regex(
                r'\((\d+)\s*k\)', item.get('name') or '', 'audio bitrate', default=None)),
        } for item in assets.get('audio_urls') or [] if url_or_none(item.get('url'))]

        for item in assets.get('urls') or []:
            video_url = url_or_none(item.get('url'))
            if video_url is None:
                continue
            ext = determine_ext(video_url)
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    video_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                fmt = item.get('name')
                formats.append({
                    'url': video_url,
                    'format': fmt,
                    'tbr': parse_bitrate(fmt),
                    'format_id': str_or_none(item.get('id')),
                    **parse_resolution(fmt),
                })

        info, token, live_title = self._search_json_ld(webpage, video_id, default={}), None, None
        if not info:
            token = self._search_regex(
                r'data\s*:\s*{action:"getAsset".*?token:\'([a-f0-9]+)\'}', webpage, 'token', default=None)
            if not token:
                live_title = get_element_by_class('unpublished-info-item future-event-title', webpage)

        if token:
            metadata = self._download_json(
                f'{base_url}/icareus-suite-api-portlet/publishing',
                video_id, fatal=False, data=urlencode_postdata({
                    'version': '03',
                    'action': 'getAsset',
                    'organizationId': organization_id,
                    'assetId': video_id,
                    'languageId': 'en_US',
                    'userId': '0',
                    'token': token,
                })) or {}
            info = {
                'title': metadata.get('name'),
                'description': metadata.get('description'),
                'timestamp': int_or_none(metadata.get('date'), scale=1000),
                'duration': int_or_none(metadata.get('duration')),
                'thumbnail': url_or_none(metadata.get('thumbnailMedium')),
            }
        elif live_title:  # Recorded livestream
            info = {
                'title': live_title,
                'description': get_element_by_class('unpublished-info-item future-event-description', webpage),
                'timestamp': int_or_none(self._search_regex(
                    r'var startEvent\s*=\s*(\d+);', webpage, 'uploadDate', fatal=False), scale=1000),
            }

        thumbnails = info.get('thumbnails') or [{
            'url': url_or_none(info.get('thumbnail') or assets.get('thumbnail')),
        }]

        return merge_dicts({
            'id': video_id,
            'title': None,
            'formats': formats,
            'subtitles': subtitles,
            'description': clean_html(info.get('description')),
            'thumbnails': thumbnails if thumbnails[0]['url'] else None,
        }, info)