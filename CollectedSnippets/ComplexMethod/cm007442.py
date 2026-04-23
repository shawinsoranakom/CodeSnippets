def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        video_path = mobj.group('path')

        if re.match(r'flash\d+v', video_path):
            video_type = 'video'
        elif video_path.startswith('iframe'):
            video_type = mobj.group('type')
            if video_type == 'swf':
                video_type = 'video'
        elif video_path.startswith('index/iframe/cast_id'):
            video_type = 'live'

        is_live = video_type == 'live'

        json_data = self._download_json(
            'http://player.rutv.ru/iframe/data%s/id/%s' % ('live' if is_live else 'video', video_id),
            video_id, 'Downloading JSON')

        if json_data['errors']:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, json_data['errors']), expected=True)

        playlist = json_data['data']['playlist']
        medialist = playlist['medialist']
        media = medialist[0]

        if media['errors']:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, media['errors']), expected=True)

        view_count = playlist.get('count_views')
        priority_transport = playlist['priority_transport']

        thumbnail = media['picture']
        width = int_or_none(media['width'])
        height = int_or_none(media['height'])
        description = media['anons']
        title = media['title']
        duration = int_or_none(media.get('duration'))

        formats = []

        for transport, links in media['sources'].items():
            for quality, url in links.items():
                preference = -1 if priority_transport == transport else -2
                if transport == 'rtmp':
                    mobj = re.search(r'^(?P<url>rtmp://[^/]+/(?P<app>.+))/(?P<playpath>.+)$', url)
                    if not mobj:
                        continue
                    fmt = {
                        'url': mobj.group('url'),
                        'play_path': mobj.group('playpath'),
                        'app': mobj.group('app'),
                        'page_url': 'http://player.rutv.ru',
                        'player_url': 'http://player.rutv.ru/flash3v/osmf.swf?i=22',
                        'rtmp_live': True,
                        'ext': 'flv',
                        'vbr': str_to_int(quality),
                        'preference': preference,
                    }
                elif transport == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        url, video_id, 'mp4', preference=preference, m3u8_id='hls'))
                    continue
                else:
                    fmt = {
                        'url': url
                    }
                fmt.update({
                    'width': width,
                    'height': height,
                    'format_id': '%s-%s' % (transport, quality),
                })
                formats.append(fmt)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'duration': duration,
            'formats': formats,
            'is_live': is_live,
        }