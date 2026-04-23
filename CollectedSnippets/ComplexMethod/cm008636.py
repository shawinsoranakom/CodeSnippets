def _real_extract(self, url):
        song_id, url_type = self._match_valid_url(url).group('id', 'type')
        item = self._call_api(url_type, {'id': song_id})

        item_id = item.get('encodeId') or song_id
        if url_type == 'video-clip':
            source = item.get('streaming')
            source['mp4'] = self._download_json(
                'http://api.mp3.zing.vn/api/mobile/video/getvideoinfo', item_id,
                query={'requestdata': json.dumps({'id': item_id})},
                note='Downloading mp4 JSON metadata').get('source')
        elif url_type == 'eps':
            source = self._call_api('episode-streaming', {'id': item_id})
        else:
            source = self._call_api('song-streaming', {'id': item_id})

        formats = []
        for k, v in (source or {}).items():
            if not v or v == 'VIP':
                continue
            if k not in ('mp4', 'hls'):
                formats.append({
                    'ext': 'mp3',
                    'format_id': k,
                    'tbr': int_or_none(k),
                    'url': self._proto_relative_url(v),
                    'vcodec': 'none',
                })
                continue
            for res, video_url in v.items():
                if not video_url:
                    continue
                if k == 'hls':
                    formats.extend(self._extract_m3u8_formats(video_url, item_id, 'mp4', m3u8_id=k, fatal=False))
                    continue
                formats.append({
                    'format_id': f'mp4-{res}',
                    'url': video_url,
                    'height': int_or_none(res),
                })

        if not formats:
            if item.get('msg') == 'Sorry, this content is not available in your country.':
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES, metadata_available=True)
            else:
                self.raise_no_formats('The song is only for VIP accounts.')

        lyric = item.get('lyric') or self._call_api('lyric', {'id': item_id}, fatal=False).get('file')

        return {
            'id': item_id,
            'title': traverse_obj(item, 'title', 'alias'),
            'thumbnail': traverse_obj(item, 'thumbnail', 'thumbnailM'),
            'duration': int_or_none(item.get('duration')),
            'track': traverse_obj(item, 'title', 'alias'),
            'artist': traverse_obj(item, 'artistsNames', 'artists_names', ('artists', 0, 'name')),
            'album': traverse_obj(item, ('album', ('name', 'title')), ('genres', 0, 'name'), get_all=False),
            'album_artist': traverse_obj(item, ('album', ('artistsNames', 'artists_names')),
                                         ('artists', 0, 'name'), get_all=False),
            'formats': formats,
            'subtitles': {'origin': [{'url': lyric}]} if lyric else None,
        }