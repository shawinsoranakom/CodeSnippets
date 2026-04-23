def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(f'{self._API_BASE}/{video_id}/private', video_id)['data']
        formats, preview_only = [], True

        for format_id, path in [
            ('preview', ['teaser', 'filepath']),
            ('transcoded', ['transcodedFilepath']),
            ('filepath', ['filepath']),
        ]:
            format_url = traverse_obj(video_data, (*path, {url_or_none}))
            if not format_url:
                continue
            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(format_url, video_id, 'mp4', m3u8_id=format_id))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'preference': -10 if format_id == 'preview' else None,
                    'quality': 10 if format_id == 'filepath' else None,
                    'height': int_or_none(
                        self._search_regex(r'_(\d{2,3}[02468])_', format_url, 'height', default=None)),
                })
            if format_id != 'preview':
                preview_only = False

        metadata = traverse_obj(
            self._download_json(f'{self._API_BASE}/{video_id}', video_id, fatal=False), 'data')
        title = traverse_obj(metadata, ('title', {clean_html}))

        if preview_only:
            title = join_nonempty(title, '(Preview)', delim=' ')
            video_id += '-preview'
            self.report_warning(
                f'Only extracting preview. Video may be paid or subscription only. {self._login_hint()}')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            **traverse_obj(metadata, {
                'description': ('description', {clean_html}),
                'uploader': ('model', 'displayName', {clean_html}),
                'thumbnail': (('screenshot', 'thumbnail'), {url_or_none}, any),
                'view_count': ('views', {parse_count}),
                'like_count': ('likes', {parse_count}),
                'release_timestamp': ('launchDate', {parse_iso8601}),
                'duration': ('videoDuration', {parse_duration}),
                'tags': ('tagList', ..., 'label', {str}, filter, all, filter),
            }),
        }