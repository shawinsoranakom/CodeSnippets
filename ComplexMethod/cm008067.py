def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_fb_webpage_and_verify(url, video_id)

        post_data = traverse_obj(
            re.findall(r'data-sjs>({.*?ScheduledServerJS.*?})</script>', webpage), (..., {json.loads}))
        data = get_first(post_data, (
            'require', ..., ..., ..., '__bbox', 'require', ..., ..., ..., (
                ('__bbox', 'result', 'data', 'ad_library_main', 'deeplink_ad_archive_result', 'deeplink_ad_archive'),
                # old path
                ('entryPointRoot', 'otherProps', 'deeplinkAdCard'),
            ), 'snapshot', {dict}))
        if not data:
            raise ExtractorError('Unable to extract ad data')

        title = data.get('title')
        if not title or title == '{{product.name}}':
            title = join_nonempty('display_format', 'page_name', delim=' by ', from_dict=data)
        markup_id = traverse_obj(data, ('body', '__m', {str}))
        markup = traverse_obj(post_data, (
            ..., 'require', ..., ..., ..., '__bbox', 'markup', lambda _, v: v[0].startswith(markup_id),
            ..., '__html', {clean_html}, {lambda x: not x.startswith('{{product.') and x}, any))

        info_dict = merge_dicts({
            'title': title,
            'description': markup or None,
        }, traverse_obj(data, {
            'description': (
                (('body', 'text'), 'link_description'),
                {lambda x: x if not x.startswith('{{product.') else None}, any),
            'uploader': ('page_name', {str}),
            'uploader_id': ('page_id', {str_or_none}),
            'uploader_url': ('page_profile_uri', {url_or_none}),
            'like_count': ('page_like_count', {int_or_none}),
        }))

        entries = []
        for idx, entry in enumerate(traverse_obj(
            data, (('videos', 'cards'), lambda _, v: any(url_or_none(v.get(f)) for f in self._FORMATS_MAP))), 1,
        ):
            entries.append({
                'id': f'{video_id}_{idx}',
                'title': entry.get('title') or title,
                'description': traverse_obj(
                    entry, 'body', 'link_description', expected_type=str) or info_dict.get('description'),
                'thumbnail': url_or_none(entry.get('video_preview_image_url')),
                'formats': self._extract_formats(entry),
            })

        if len(entries) == 1:
            info_dict.update(entries[0])

        elif len(entries) > 1:
            info_dict.update({
                'title': entries[0]['title'],
                'entries': entries,
                '_type': 'playlist',
            })

        info_dict['id'] = video_id

        return info_dict