def _extract_video_info(self, video, fatal=True):
        video_id = video['videoId']

        formats = []
        refs = traverse_obj(video, 'refs', expected_type=dict) or {}

        m3u8_url = url_or_none(refs.get('m3uUrl'))
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))

        f4m_url = url_or_none(refs.get('f4mUrl'))
        if f4m_url:
            formats.extend(self._extract_f4m_formats(
                f4m_url, video_id, f4m_id='hds', fatal=False))

        for asset in (video.get('assets') or []):
            asset_url = url_or_none(asset.get('url'))
            if not asset_url:
                continue
            formats.append({
                'url': asset_url,
                'tbr': int_or_none(asset.get('bitrate'), 1000),
                'fps': int_or_none(asset.get('frame_rate')),
                'height': int_or_none(asset.get('height')),
                'width': int_or_none(asset.get('width')),
            })

        mezzanine_url = traverse_obj(
            video, ('system', 'mezzanineUrl'), expected_type=url_or_none)
        if mezzanine_url:
            formats.append({
                'ext': determine_ext(mezzanine_url, 'mp4'),
                'format_id': 'mezzanine',
                'preference': 1,
                'url': mezzanine_url,
            })

        if formats or fatal:
            self._sort_formats(formats)
        else:
            return

        thumbnails = traverse_obj(
            video, ('thumbnails', Ellipsis, {'url': 'url'}), expected_type=url_or_none)
        tags = traverse_obj(
            video, ('tags', Ellipsis, 'displayName'),
            expected_type=lambda x: x.strip() or None)

        metadata = traverse_obj(video, 'metadata', expected_type=dict) or {}
        title = traverse_obj(
            metadata, 'longTitle', 'title', 'name',
            expected_type=lambda x: x.strip() or None)

        return {
            'id': video_id,
            'title': title,
            'description': strip_or_none(metadata.get('description')),
            'timestamp': parse_iso8601(metadata.get('publishDate')),
            'duration': int_or_none(metadata.get('duration')),
            'thumbnails': thumbnails,
            'formats': formats,
            'tags': tags,
        }