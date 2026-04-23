def _real_extract(self, url):
        uploader_id, work_id = self._match_valid_url(url).group('uploader_id', 'id')
        try:
            works = self._call_api(uploader_id, work_id)
        except ExtractorError as e:
            if not isinstance(e.cause, HTTPError) or e.cause.status != 429:
                raise
            webpage = e.cause.response.read().decode()
            value = self._search_regex(
                r'document\.cookie\s*=\s*["\']request_key=([^;"\']+)', webpage, 'request key')
            self._set_cookie('skeb.jp', 'request_key', value)
            works = self._call_api(uploader_id, work_id)

        info = {
            'uploader_id': uploader_id,
            **traverse_obj(works, {
                'age_limit': ('nsfw', {bool}, {lambda x: 18 if x else None}),
                'description': (('source_body', 'body'), {clean_html}, filter, any),
                'genres': ('genre', {str}, filter, all, filter),
                'tags': ('tag_list', ..., {str}, filter, all, filter),
                'uploader': ('creator', 'name', {str}),
            }),
        }

        entries = []
        for idx, preview in enumerate(traverse_obj(works, ('previews', lambda _, v: url_or_none(v['url']))), 1):
            ext = traverse_obj(preview, ('information', 'extension', {str}))
            if ext not in ('mp3', 'mp4', 'wav'):
                self.report_warning(f'Skipping unsupported extension "{ext}"')
                continue

            entries.append({
                'ext': ext,
                'title': f'{work_id}-{idx}',
                'subtitles': {
                    'ja': [{
                        'ext': 'vtt',
                        'url': preview['vtt_url'],
                    }],
                } if url_or_none(preview.get('vtt_url')) else None,
                'vcodec': 'none' if ext in ('mp3', 'wav') else None,
                **info,
                **traverse_obj(preview, {
                    'id': ('id', {str_or_none}),
                    'thumbnail': ('poster_url', {url_or_none}),
                    'url': ('url', {url_or_none}),
                }),
                **traverse_obj(preview, ('information', {
                    'duration': ('duration', {int_or_none}),
                    'fps': ('frame_rate', {int_or_none}),
                    'height': ('height', {int_or_none}),
                    'width': ('width', {int_or_none}),
                })),
            })

        return self.playlist_result(entries, work_id, **info)