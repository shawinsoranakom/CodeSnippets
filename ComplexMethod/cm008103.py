def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id=video_id, headers={'Referer': url})
        video_data = self._search_nextjs_data(webpage, video_id)['props']['pageProps']['detail']['video']

        data = self._download_json(
            f'https://mod-api.xinpianchang.com/mod/api/v2/media/{video_data["vid"]}', video_id,
            query={'appKey': video_data['appKey']})['data']
        formats, subtitles = [], {}
        for k, v in data.get('resource').items():
            if k in ('dash', 'hls'):
                v_url = v.get('url')
                if not v_url:
                    continue
                if k == 'dash':
                    fmts, subs = self._extract_mpd_formats_and_subtitles(v_url, video_id=video_id)
                elif k == 'hls':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(v_url, video_id=video_id)
                formats.extend(fmts)
                subtitles = self._merge_subtitles(subtitles, subs)
            elif k == 'progressive':
                formats.extend([{
                    'url': url_or_none(prog.get('url')),
                    'width': int_or_none(prog.get('width')),
                    'height': int_or_none(prog.get('height')),
                    'ext': 'mp4',
                    'http_headers': {
                        # NB: Server returns 403 without the Range header
                        'Range': 'bytes=0-',
                    },
                } for prog in v if prog.get('url') or []])

        return {
            'id': video_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'duration': int_or_none(data.get('duration')),
            'categories': data.get('categories'),
            'tags': data.get('keywords'),
            'thumbnail': data.get('cover'),
            'uploader': try_get(data, lambda x: x['owner']['username']),
            'uploader_id': str_or_none(try_get(data, lambda x: x['owner']['id'])),
            'formats': formats,
            'subtitles': subtitles,
        }