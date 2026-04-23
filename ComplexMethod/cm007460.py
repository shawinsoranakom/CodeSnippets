def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = re.match(self._VALID_URL, url)
        host, video_id = mobj.group('custom_host') or mobj.group('host'), mobj.group('id')

        headers = {}
        query = {
            'id': video_id,
        }

        referrer = smuggled_data.get('referrer')
        if referrer:
            headers['Referer'] = referrer
            query['referrer'] = referrer

        player_data = self._download_json(
            'http://%s/api/player_data' % host, video_id,
            headers=headers, query=query)

        media = player_data['data']['playlist']['viewports'][0]['medialist'][0]

        title = media['title']
        description = media.get('description')
        thumbnail = self._proto_relative_url(media.get('snapshot'), 'http:')
        duration = int_or_none(media.get('duration'))
        view_count = int_or_none(media.get('views'))

        age_restriction = media.get('age_restriction')
        age_limit = None
        if age_restriction:
            age_limit = 0 if age_restriction == 'allow_all' else 18

        secure_m3u8 = self._proto_relative_url(media['sources']['secure_m3u8']['auto'], 'http:')

        formats = []

        m3u8_url = self._get_video_url(secure_m3u8, video_id, 'Downloading m3u8 JSON')
        m3u8_formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls', fatal=False)
        formats.extend(m3u8_formats)

        m3u8_formats_dict = {}
        for f in m3u8_formats:
            if f.get('height') is not None:
                m3u8_formats_dict[f['height']] = f

        mp4_data = self._download_json(
            # Secure mp4 URL is constructed according to Player.prototype.mp4 from
            # http://lentaru.media.eagleplatform.com/player/player.js
            re.sub(r'm3u8|hlsvod|hls|f4m', 'mp4s', secure_m3u8),
            video_id, 'Downloading mp4 JSON', fatal=False)
        if mp4_data:
            for format_id, format_url in mp4_data.get('data', {}).items():
                if not url_or_none(format_url):
                    continue
                height = int_or_none(format_id)
                if height is not None and m3u8_formats_dict.get(height):
                    f = m3u8_formats_dict[height].copy()
                    f.update({
                        'format_id': f['format_id'].replace('hls', 'http'),
                        'protocol': 'http',
                    })
                else:
                    f = {
                        'format_id': 'http-%s' % format_id,
                        'height': int_or_none(format_id),
                    }
                f['url'] = format_url
                formats.append(f)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'age_limit': age_limit,
            'formats': formats,
        }