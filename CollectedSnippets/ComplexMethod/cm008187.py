def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'https://www.imdb.com/video/vi{video_id}', video_id)
        info = self._search_nextjs_data(webpage, video_id)
        video_info = traverse_obj(info, ('props', 'pageProps', 'videoPlaybackData', 'video'), default={})
        title = (traverse_obj(video_info, ('name', 'value'), ('primaryTitle', 'titleText', 'text'))
                 or self._html_search_meta(('og:title', 'twitter:title'), webpage, default=None)
                 or self._html_extract_title(webpage))
        data = video_info.get('playbackURLs') or try_get(self._download_json(
            'https://www.imdb.com/ve/data/VIDEO_PLAYBACK_DATA', video_id,
            query={
                'key': base64.b64encode(json.dumps({
                    'type': 'VIDEO_PLAYER',
                    'subType': 'FORCE_LEGACY',
                    'id': f'vi{video_id}',
                }).encode()).decode(),
            }), lambda x: x[0]['videoLegacyEncodings'])
        quality = qualities(('SD', '480p', '720p', '1080p'))
        formats, subtitles = [], {}
        for encoding in data:
            if not encoding or not isinstance(encoding, dict):
                continue
            video_url = url_or_none(encoding.get('url'))
            if not video_url:
                continue
            ext = mimetype2ext(encoding.get(
                'mimeType')) or determine_ext(video_url)
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    preference=1, m3u8_id='hls', fatal=False)
                subtitles = self._merge_subtitles(subtitles, subs)
                formats.extend(fmts)
                continue
            format_id = traverse_obj(encoding, ('displayName', 'value'), 'definition')
            formats.append({
                'format_id': format_id,
                'url': video_url,
                'ext': ext,
                'quality': quality(format_id),
            })

        return {
            'id': video_id,
            'title': title,
            'alt_title': info.get('videoSubTitle'),
            'formats': formats,
            'description': try_get(video_info, lambda x: x['description']['value']),
            'thumbnail': url_or_none(try_get(video_info, lambda x: x['thumbnail']['url'])),
            'duration': int_or_none(try_get(video_info, lambda x: x['runtime']['value'])),
            'subtitles': subtitles,
        }