def extract_formats(self, info):
        err = 0
        formats = []
        song_id = info['id']
        for song_format in self._FORMATS:
            details = info.get(song_format)
            if not details:
                continue

            bitrate = int_or_none(details.get('bitrate')) or 999000
            data = self._call_player_api(song_id, bitrate)
            for song in try_get(data, lambda x: x['data'], list) or []:
                song_url = try_get(song, lambda x: x['url'])
                if not song_url:
                    continue
                if self._is_valid_url(song_url, info['id'], 'song'):
                    formats.append({
                        'url': song_url,
                        'ext': details.get('extension'),
                        'abr': float_or_none(song.get('br'), scale=1000),
                        'format_id': song_format,
                        'filesize': int_or_none(song.get('size')),
                        'asr': int_or_none(details.get('sr')),
                    })
                elif err == 0:
                    err = try_get(song, lambda x: x['code'], int)

        if not formats:
            msg = 'No media links found'
            if err != 0 and (err < 200 or err >= 400):
                raise ExtractorError(
                    '%s (site code %d)' % (msg, err, ), expected=True)
            else:
                self.raise_geo_restricted(
                    msg + ': probably this video is not available from your location due to geo restriction.',
                    countries=['CN'])

        return formats