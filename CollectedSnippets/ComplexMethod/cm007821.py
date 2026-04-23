def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        host = mobj.group('host')
        appname = self._HOST_TO_APPNAME[host] if host else mobj.group('appname')
        vendor = self._APP_NAME_TO_VENDOR[appname]

        data = self._download_json(
            'http://svp.vg.no/svp/api/v1/%s/assets/%s?appName=%s-website'
            % (vendor, video_id, appname),
            video_id, 'Downloading media JSON')

        if data.get('status') == 'inactive':
            raise ExtractorError(
                'Video %s is no longer available' % video_id, expected=True)

        info = {
            'formats': [],
        }
        if len(video_id) == 5:
            if appname == 'bttv':
                info = self._extract_video_info('btno', video_id)

        streams = data['streamUrls']
        stream_type = data.get('streamType')
        is_live = stream_type == 'live'
        formats = []

        hls_url = streams.get('hls')
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4',
                entry_protocol='m3u8' if is_live else 'm3u8_native',
                m3u8_id='hls', fatal=False))

        hds_url = streams.get('hds')
        if hds_url:
            hdcore_sign = 'hdcore=3.7.0'
            f4m_formats = self._extract_f4m_formats(
                hds_url + '?%s' % hdcore_sign, video_id, f4m_id='hds', fatal=False)
            if f4m_formats:
                for entry in f4m_formats:
                    # URLs without the extra param induce an 404 error
                    entry.update({'extra_param_to_segment_url': hdcore_sign})
                    formats.append(entry)

        mp4_urls = streams.get('pseudostreaming') or []
        mp4_url = streams.get('mp4')
        if mp4_url:
            mp4_urls.append(mp4_url)
        for mp4_url in mp4_urls:
            format_info = {
                'url': mp4_url,
            }
            mobj = re.search(r'(\d+)_(\d+)_(\d+)', mp4_url)
            if mobj:
                tbr = int(mobj.group(3))
                format_info.update({
                    'width': int(mobj.group(1)),
                    'height': int(mobj.group(2)),
                    'tbr': tbr,
                    'format_id': 'mp4-%s' % tbr,
                })
            formats.append(format_info)

        info['formats'].extend(formats)

        if not info['formats']:
            properties = try_get(
                data, lambda x: x['streamConfiguration']['properties'], list)
            if properties and 'geoblocked' in properties:
                raise self.raise_geo_restricted(
                    countries=[host.rpartition('.')[-1].partition('/')[0].upper()])

        self._sort_formats(info['formats'])

        info.update({
            'id': video_id,
            'title': self._live_title(data['title']) if is_live else data['title'],
            'description': data['description'],
            'thumbnail': data['images']['main'] + '?t[]=900x506q80',
            'timestamp': data['published'],
            'duration': float_or_none(data['duration'], 1000),
            'view_count': data['displays'],
            'is_live': is_live,
        })
        return info