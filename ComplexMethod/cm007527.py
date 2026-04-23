def _extract_sdn_formats(self, sdn_url, video_id):
        sdn_data = self._download_json(sdn_url, video_id)

        if sdn_data.get('Location'):
            sdn_url = sdn_data['Location']
            sdn_data = self._download_json(sdn_url, video_id)

        formats = []
        mp4_formats = try_get(sdn_data, lambda x: x['data']['mp4'], dict) or {}
        for format_id, format_data in mp4_formats.items():
            relative_url = format_data.get('url')
            if not relative_url:
                continue

            try:
                width, height = format_data.get('resolution')
            except (TypeError, ValueError):
                width, height = None, None

            f = {
                'url': urljoin(sdn_url, relative_url),
                'format_id': 'http-%s' % format_id,
                'tbr': int_or_none(format_data.get('bandwidth'), scale=1000),
                'width': int_or_none(width),
                'height': int_or_none(height),
            }
            f.update(parse_codecs(format_data.get('codec')))
            formats.append(f)

        pls = sdn_data.get('pls', {})

        def get_url(format_id):
            return try_get(pls, lambda x: x[format_id]['url'], compat_str)

        dash_rel_url = get_url('dash')
        if dash_rel_url:
            formats.extend(self._extract_mpd_formats(
                urljoin(sdn_url, dash_rel_url), video_id, mpd_id='dash',
                fatal=False))

        hls_rel_url = get_url('hls')
        if hls_rel_url:
            formats.extend(self._extract_m3u8_formats(
                urljoin(sdn_url, hls_rel_url), video_id, ext='mp4',
                m3u8_id='hls', fatal=False))

        self._sort_formats(formats)
        return formats