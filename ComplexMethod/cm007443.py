def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'https://ben.slideslive.com/player/' + video_id, video_id)
        service_name = video_data['video_service_name'].lower()
        assert service_name in ('url', 'yoda', 'vimeo', 'youtube')
        service_id = video_data['video_service_id']
        subtitles = {}
        for sub in try_get(video_data, lambda x: x['subtitles'], list) or []:
            if not isinstance(sub, dict):
                continue
            webvtt_url = url_or_none(sub.get('webvtt_url'))
            if not webvtt_url:
                continue
            lang = sub.get('language') or 'en'
            subtitles.setdefault(lang, []).append({
                'url': webvtt_url,
            })
        info = {
            'id': video_id,
            'thumbnail': video_data.get('thumbnail'),
            'is_live': bool_or_none(video_data.get('is_live')),
            'subtitles': subtitles,
        }
        if service_name in ('url', 'yoda'):
            info['title'] = video_data['title']
            if service_name == 'url':
                info['url'] = service_id
            else:
                formats = []
                _MANIFEST_PATTERN = 'https://01.cdn.yoda.slideslive.com/%s/master.%s'
                # use `m3u8` entry_protocol until EXT-X-MAP is properly supported by `m3u8_native` entry_protocol
                formats.extend(self._extract_m3u8_formats(
                    _MANIFEST_PATTERN % (service_id, 'm3u8'),
                    service_id, 'mp4', m3u8_id='hls', fatal=False))
                formats.extend(self._extract_mpd_formats(
                    _MANIFEST_PATTERN % (service_id, 'mpd'), service_id,
                    mpd_id='dash', fatal=False))
                self._sort_formats(formats)
                info.update({
                    'id': service_id,
                    'formats': formats,
                })
        else:
            info.update({
                '_type': 'url_transparent',
                'url': service_id,
                'ie_key': service_name.capitalize(),
                'title': video_data.get('title'),
            })
            if service_name == 'vimeo':
                info['url'] = smuggle_url(
                    'https://player.vimeo.com/video/' + service_id,
                    {'http_headers': {'Referer': url}})
        return info