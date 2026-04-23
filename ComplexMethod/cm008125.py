def _real_extract(self, url):
        video_id = self._match_id(url)

        details = self._call_api(video_id)
        source = traverse_obj(details, ('vod', 'source', 'mediasource', {dict})) or {}

        formats = []
        for stream in traverse_obj(details, (
            'vod', 'source', 'mediasourcelist', lambda _, v: v['mediaurl'] or v['mediarscuse'],
        ), default=[source]):
            if not stream.get('mediaurl'):
                new_source = traverse_obj(
                    self._call_api(video_id, rscuse=stream['mediarscuse']),
                    ('vod', 'source', 'mediasource', {dict})) or {}
                if new_source.get('mediarscuse') == source.get('mediarscuse') or not new_source.get('mediaurl'):
                    continue
                stream = new_source
            formats.append({
                'url': stream['mediaurl'],
                'format_id': stream.get('mediarscuse'),
                'format_note': stream.get('medianame'),
                **parse_resolution(stream.get('quality')),
                'preference': int_or_none(stream.get('mediarscuse')),
            })

        caption_url = traverse_obj(details, ('vod', 'source', 'subtitle', {url_or_none}))

        return {
            'id': video_id,
            **traverse_obj(details, ('vod', {
                'title': ('info', 'title'),
                'duration': ('info', 'duration', {int_or_none}),
                'view_count': ('info', 'viewcount', {int_or_none}),
                'like_count': ('info', 'likecount', {int_or_none}),
                'description': ('info', 'synopsis', {clean_html}),
                'episode': ('info', 'content', ('contenttitle', 'title')),
                'episode_number': ('info', 'content', 'number', {int_or_none}),
                'series': ('info', 'program', 'programtitle'),
                'age_limit': ('info', 'targetage', {int_or_none}),
                'release_timestamp': ('info', 'broaddate', {parse_iso8601}),
                'thumbnail': ('source', 'thumbnail', 'origin', {url_or_none}),
            }), get_all=False),
            'formats': formats,
            'subtitles': {'ko': [{'url': caption_url}]} if caption_url else None,
        }