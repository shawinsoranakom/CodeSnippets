def _real_extract(self, url):
        video_id = self._match_id(url)

        coub = self._download_json(
            f'http://coub.com/api/v2/coubs/{video_id}.json', video_id)

        if coub.get('error'):
            raise ExtractorError(
                '{} said: {}'.format(self.IE_NAME, coub['error']), expected=True)

        title = coub['title']

        file_versions = coub['file_versions']

        QUALITIES = ('low', 'med', 'high', 'higher')

        MOBILE = 'mobile'
        IPHONE = 'iphone'
        HTML5 = 'html5'

        SOURCE_PREFERENCE = (MOBILE, IPHONE, HTML5)

        quality_key = qualities(QUALITIES)
        preference_key = qualities(SOURCE_PREFERENCE)

        formats = []

        for kind, items in file_versions.get(HTML5, {}).items():
            if kind not in ('video', 'audio'):
                continue
            if not isinstance(items, dict):
                continue
            for quality, item in items.items():
                if not isinstance(item, dict):
                    continue
                item_url = item.get('url')
                if not item_url:
                    continue
                formats.append({
                    'url': item_url,
                    'format_id': f'{HTML5}-{kind}-{quality}',
                    'filesize': int_or_none(item.get('size')),
                    'vcodec': 'none' if kind == 'audio' else None,
                    'acodec': 'none' if kind == 'video' else None,
                    'quality': quality_key(quality),
                    'source_preference': preference_key(HTML5),
                })

        iphone_url = file_versions.get(IPHONE, {}).get('url')
        if iphone_url:
            formats.append({
                'url': iphone_url,
                'format_id': IPHONE,
                'source_preference': preference_key(IPHONE),
            })

        mobile_url = file_versions.get(MOBILE, {}).get('audio_url')
        if mobile_url:
            formats.append({
                'url': mobile_url,
                'format_id': f'{MOBILE}-audio',
                'source_preference': preference_key(MOBILE),
            })

        thumbnail = coub.get('picture')
        duration = float_or_none(coub.get('duration'))
        timestamp = parse_iso8601(coub.get('published_at') or coub.get('created_at'))
        uploader = coub.get('channel', {}).get('title')
        uploader_id = coub.get('channel', {}).get('permalink')

        view_count = int_or_none(coub.get('views_count') or coub.get('views_increase_count'))
        like_count = int_or_none(coub.get('likes_count'))
        repost_count = int_or_none(coub.get('recoubs_count'))

        age_restricted = coub.get('age_restricted', coub.get('age_restricted_by_admin'))
        if age_restricted is not None:
            age_limit = 18 if age_restricted is True else 0
        else:
            age_limit = None

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'like_count': like_count,
            'repost_count': repost_count,
            'age_limit': age_limit,
            'formats': formats,
        }