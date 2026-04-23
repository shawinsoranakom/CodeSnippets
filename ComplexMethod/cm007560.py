def _talk_info(self, url, video_name):
        webpage = self._download_webpage(url, video_name)

        info = self._extract_info(webpage)

        data = try_get(info, lambda x: x['__INITIAL_DATA__'], dict) or info
        talk_info = data['talks'][0]

        title = talk_info['title'].strip()

        downloads = talk_info.get('downloads') or {}
        native_downloads = downloads.get('nativeDownloads') or talk_info.get('nativeDownloads') or {}

        formats = [{
            'url': format_url,
            'format_id': format_id,
        } for (format_id, format_url) in native_downloads.items() if format_url is not None]

        subtitled_downloads = downloads.get('subtitledDownloads') or {}
        for lang, subtitled_download in subtitled_downloads.items():
            for q in self._NATIVE_FORMATS:
                q_url = subtitled_download.get(q)
                if not q_url:
                    continue
                formats.append({
                    'url': q_url,
                    'format_id': '%s-%s' % (q, lang),
                    'language': lang,
                })

        if formats:
            for f in formats:
                finfo = self._NATIVE_FORMATS.get(f['format_id'].split('-')[0])
                if finfo:
                    f.update(finfo)

        player_talk = talk_info['player_talks'][0]

        resources_ = player_talk.get('resources') or talk_info.get('resources')

        http_url = None
        for format_id, resources in resources_.items():
            if format_id == 'hls':
                if not isinstance(resources, dict):
                    continue
                stream_url = url_or_none(resources.get('stream'))
                if not stream_url:
                    continue
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_name, 'mp4', m3u8_id=format_id,
                    fatal=False))
            else:
                if not isinstance(resources, list):
                    continue
                if format_id == 'h264':
                    for resource in resources:
                        h264_url = resource.get('file')
                        if not h264_url:
                            continue
                        bitrate = int_or_none(resource.get('bitrate'))
                        formats.append({
                            'url': h264_url,
                            'format_id': '%s-%sk' % (format_id, bitrate),
                            'tbr': bitrate,
                        })
                        if re.search(r'\d+k', h264_url):
                            http_url = h264_url
                elif format_id == 'rtmp':
                    streamer = talk_info.get('streamer')
                    if not streamer:
                        continue
                    for resource in resources:
                        formats.append({
                            'format_id': '%s-%s' % (format_id, resource.get('name')),
                            'url': streamer,
                            'play_path': resource['file'],
                            'ext': 'flv',
                            'width': int_or_none(resource.get('width')),
                            'height': int_or_none(resource.get('height')),
                            'tbr': int_or_none(resource.get('bitrate')),
                        })

        m3u8_formats = list(filter(
            lambda f: f.get('protocol') == 'm3u8' and f.get('vcodec') != 'none',
            formats))
        if http_url:
            for m3u8_format in m3u8_formats:
                bitrate = self._search_regex(r'(\d+k)', m3u8_format['url'], 'bitrate', default=None)
                if not bitrate:
                    continue
                bitrate_url = re.sub(r'\d+k', bitrate, http_url)
                if not self._is_valid_url(
                        bitrate_url, video_name, '%s bitrate' % bitrate):
                    continue
                f = m3u8_format.copy()
                f.update({
                    'url': bitrate_url,
                    'format_id': m3u8_format['format_id'].replace('hls', 'http'),
                    'protocol': 'http',
                })
                if f.get('acodec') == 'none':
                    del f['acodec']
                formats.append(f)

        audio_download = talk_info.get('audioDownload')
        if audio_download:
            formats.append({
                'url': audio_download,
                'format_id': 'audio',
                'vcodec': 'none',
            })

        if not formats:
            external = player_talk.get('external')
            if isinstance(external, dict):
                service = external.get('service')
                if isinstance(service, compat_str):
                    ext_url = None
                    if service.lower() == 'youtube':
                        ext_url = external.get('code')
                    return self.url_result(ext_url or external['uri'])

        self._sort_formats(formats)

        video_id = compat_str(talk_info['id'])

        return {
            'id': video_id,
            'title': title,
            'uploader': player_talk.get('speaker') or talk_info.get('speaker'),
            'thumbnail': player_talk.get('thumb') or talk_info.get('thumb'),
            'description': self._og_search_description(webpage),
            'subtitles': self._get_subtitles(video_id, talk_info),
            'formats': formats,
            'duration': float_or_none(talk_info.get('duration')),
            'view_count': int_or_none(data.get('viewed_count')),
            'comment_count': int_or_none(
                try_get(data, lambda x: x['comments']['count'])),
            'tags': try_get(talk_info, lambda x: x['tags'], list),
        }