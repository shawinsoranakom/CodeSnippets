def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'http://swrmediathek.de/AjaxEntry?ekey=%s' % video_id,
            video_id, 'Downloading video JSON')

        attr = video['attr']
        title = attr['entry_title']
        media_type = attr.get('entry_etype')

        formats = []
        for entry in video.get('sub', []):
            if entry.get('name') != 'entry_media':
                continue

            entry_attr = entry.get('attr', {})
            f_url = entry_attr.get('val2')
            if not f_url:
                continue
            codec = entry_attr.get('val0')
            if codec == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    f_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif codec == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    f_url + '?hdcore=3.7.0', video_id,
                    f4m_id='hds', fatal=False))
            else:
                formats.append({
                    'format_id': determine_protocol({'url': f_url}),
                    'url': f_url,
                    'quality': int_or_none(entry_attr.get('val1')),
                    'vcodec': codec if media_type == 'Video' else 'none',
                    'acodec': codec if media_type == 'Audio' else None,
                })
        self._sort_formats(formats)

        upload_date = None
        entry_pdatet = attr.get('entry_pdatet')
        if entry_pdatet:
            upload_date = entry_pdatet[:-4]

        return {
            'id': video_id,
            'title': title,
            'description': attr.get('entry_descl'),
            'thumbnail': attr.get('entry_image_16_9'),
            'duration': parse_duration(attr.get('entry_durat')),
            'upload_date': upload_date,
            'uploader': attr.get('channel_title'),
            'uploader_id': attr.get('channel_idkey'),
            'formats': formats,
        }