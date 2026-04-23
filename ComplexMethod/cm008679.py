def _real_extract(self, url):
        video_id = self._match_id(url)
        video_info = traverse_obj(
            self._call_api('get', video_id, {'id': video_id, 'flags': self._maximum_flags}),
            ('items', 0, {dict}))

        source = video_info.get('image')
        if not source or not source.endswith('mp4'):
            self.raise_no_formats('Could not extract a video', expected=bool(source), video_id=video_id)

        metadata = self._call_api('info', video_id, {'itemId': video_id}, note='Downloading tags')
        tags = traverse_obj(metadata, ('tags', ..., 'tag', {str}))
        # Sorted by "confidence", higher confidence = earlier in list
        confidences = traverse_obj(metadata, ('tags', ..., 'confidence', ({int}, {float})))
        if confidences:
            tags = [tag for _, tag in sorted(zip(confidences, tags), reverse=True)]  # noqa: B905

        formats = traverse_obj(video_info, ('variants', ..., {
            'format_id': ('name', {str}),
            'url': ('path', {self._create_source_url}),
            'ext': ('mimeType', {mimetype2ext}),
            'vcodec': ('codec', {str}),
            'width': ('width', {int_or_none}),
            'height': ('height', {int_or_none}),
            'bitrate': ('bitRate', {float_or_none}),
            'filesize': ('fileSize', {int_or_none}),
        })) if video_info.get('variants') else [{
            'ext': 'mp4',
            'format_id': 'source',
            **traverse_obj(video_info, {
                'url': ('image', {self._create_source_url}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
            }),
        }]

        subtitles = {}
        for subtitle in traverse_obj(video_info, ('subtitles', lambda _, v: v['language'])):
            subtitles.setdefault(subtitle['language'], []).append(traverse_obj(subtitle, {
                'url': ('path', {self._create_source_url}),
                'note': ('label', {str}),
            }))

        return {
            'id': video_id,
            'title': f'pr0gramm-{video_id} by {video_info.get("user")}',
            'tags': tags,
            'formats': formats,
            'subtitles': subtitles,
            'age_limit': 18 if traverse_obj(video_info, ('flags', {0b110.__and__})) else 0,
            '_old_archive_ids': [make_archive_id('Pr0grammStatic', video_id)],
            **traverse_obj(video_info, {
                'uploader': ('user', {str}),
                'uploader_id': ('userId', {str_or_none}),
                'like_count': ('up', {int}),
                'dislike_count': ('down', {int}),
                'timestamp': ('created', {int}),
                'upload_date': ('created', {int}, {dt.date.fromtimestamp}, {lambda x: x.strftime('%Y%m%d')}),
                'thumbnail': ('thumb', {urljoin('https://thumb.pr0gramm.com')}),
            }),
        }