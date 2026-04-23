def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        video = self._download_json(
            'https://api.byutv.org/api3/catalog/getvideosforcontent',
            display_id, query={
                'contentid': video_id,
                'channel': 'byutv',
                'x-byutv-context': 'web$US',
            }, headers={
                'x-byutv-context': 'web$US',
                'x-byutv-platformkey': 'xsaaw9c7y5',
            })

        ep = video.get('ooyalaVOD')
        if ep:
            return {
                '_type': 'url_transparent',
                'ie_key': 'Ooyala',
                'url': 'ooyala:%s' % ep['providerId'],
                'id': video_id,
                'display_id': display_id,
                'title': ep.get('title'),
                'description': ep.get('description'),
                'thumbnail': ep.get('imageThumbnail'),
            }

        info = {}
        formats = []
        for format_id, ep in video.items():
            if not isinstance(ep, dict):
                continue
            video_url = url_or_none(ep.get('videoUrl'))
            if not video_url:
                continue
            ext = determine_ext(video_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    video_url, video_id, mpd_id='dash', fatal=False))
            else:
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                })
            merge_dicts(info, {
                'title': ep.get('title'),
                'description': ep.get('description'),
                'thumbnail': ep.get('imageThumbnail'),
                'duration': parse_duration(ep.get('length')),
            })
        self._sort_formats(formats)

        return merge_dicts(info, {
            'id': video_id,
            'display_id': display_id,
            'title': display_id,
            'formats': formats,
        })