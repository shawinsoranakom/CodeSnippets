def _real_extract(self, url):
        org, uuid = self._match_valid_url(url).groups()
        for orgs, tmpl in self._POWA_DEFAULTS:
            if org in orgs:
                base_api_tmpl = tmpl
                break
        else:
            base_api_tmpl = '%s-prod-cdn.video-api.arcpublishing.com/api'
        if org == 'wapo':
            org = 'washpost'
        video = self._download_json(
            'https://%s/v1/ansvideos/findByUuid' % (base_api_tmpl % org),
            uuid, query={'uuid': uuid})[0]
        title = video['headlines']['basic']
        is_live = video.get('status') == 'live'

        urls = []
        formats = []
        for s in video.get('streams', []):
            s_url = s.get('url')
            if not s_url or s_url in urls:
                continue
            urls.append(s_url)
            stream_type = s.get('stream_type')
            if stream_type == 'smil':
                smil_formats = self._extract_smil_formats(
                    s_url, uuid, fatal=False)
                for f in smil_formats:
                    if f['url'].endswith('/cfx/st'):
                        f['app'] = 'cfx/st'
                        if not f['play_path'].startswith('mp4:'):
                            f['play_path'] = 'mp4:' + f['play_path']
                        if isinstance(f['tbr'], float):
                            f['vbr'] = f['tbr'] * 1000
                            del f['tbr']
                            f['format_id'] = 'rtmp-%d' % f['vbr']
                formats.extend(smil_formats)
            elif stream_type in ('ts', 'hls'):
                m3u8_formats = self._extract_m3u8_formats(
                    s_url, uuid, 'mp4', live=is_live, m3u8_id='hls', fatal=False)
                if all(f.get('acodec') == 'none' for f in m3u8_formats):
                    continue
                for f in m3u8_formats:
                    height = f.get('height')
                    if not height:
                        continue
                    vbr = self._search_regex(
                        r'[_x]%d[_-](\d+)' % height, f['url'], 'vbr', default=None)
                    if vbr:
                        f['vbr'] = int(vbr)
                formats.extend(m3u8_formats)
            else:
                vbr = int_or_none(s.get('bitrate'))
                formats.append({
                    'format_id': join_nonempty(stream_type, vbr),
                    'vbr': vbr,
                    'width': int_or_none(s.get('width')),
                    'height': int_or_none(s.get('height')),
                    'filesize': int_or_none(s.get('filesize')),
                    'url': s_url,
                    'quality': -10,
                })

        subtitles = {}
        for subtitle in (try_get(video, lambda x: x['subtitles']['urls'], list) or []):
            subtitle_url = subtitle.get('url')
            if subtitle_url:
                subtitles.setdefault('en', []).append({'url': subtitle_url})

        return {
            'id': uuid,
            'title': title,
            'thumbnail': try_get(video, lambda x: x['promo_image']['url']),
            'description': try_get(video, lambda x: x['subheadlines']['basic']),
            'formats': formats,
            'duration': int_or_none(video.get('duration'), 100),
            'timestamp': parse_iso8601(video.get('created_date')),
            'subtitles': subtitles,
            'is_live': is_live,
        }