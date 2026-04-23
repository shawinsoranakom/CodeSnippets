def _real_extract(self, url):
        post_id = self._match_id(url)
        webpage = self._download_webpage(url, post_id)
        api_data = self._call_api(f'post/{post_id}?incl="poststats|userinfo"', post_id)

        post_data = api_data.get('data')
        user_data = try_get(api_data, lambda x: x['aux']['uinf'][post_data['uid']], dict) or {}

        vid = post_data.get('vid')
        ovid = post_data.get('ovid')

        if post_data.get('p_type') == 'stream':
            return self.url_result(f'https://gettr.com/streaming/{post_id}', ie='GettrStreaming', video_id=post_id)

        if not (ovid or vid):
            embed_url = url_or_none(post_data.get('prevsrc'))
            shared_post_id = traverse_obj(api_data, ('aux', 'shrdpst', '_id'), ('data', 'rpstIds', 0), expected_type=str)

            if embed_url:
                return self.url_result(embed_url)
            elif shared_post_id:
                return self.url_result(f'https://gettr.com/post/{shared_post_id}', ie='Gettr', video_id=shared_post_id)
            else:
                raise ExtractorError('There\'s no video in this post.')

        title = description = str_or_none(
            post_data.get('txt') or self._og_search_description(webpage))

        uploader = str_or_none(
            user_data.get('nickname')
            or self._search_regex(r'^(.+?) on GETTR', self._og_search_title(webpage, default=''), 'uploader', fatal=False))

        if uploader:
            title = f'{uploader} - {title}'

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            urljoin(self._MEDIA_BASE_URL, vid), post_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls', fatal=False) if vid else ([], {})

        if ovid:
            formats.append({
                'url': urljoin(self._MEDIA_BASE_URL, ovid),
                'format_id': 'ovid',
                'ext': 'mp4',
                'width': int_or_none(post_data.get('vid_wid')),
                'height': int_or_none(post_data.get('vid_hgt')),
            })

        return {
            'id': post_id,
            'title': title,
            'description': description,
            'formats': formats,
            'subtitles': subtitles,
            'uploader': uploader,
            'uploader_id': str_or_none(
                dict_get(user_data, ['_id', 'username'])
                or post_data.get('uid')),
            'thumbnail': url_or_none(
                urljoin(self._MEDIA_BASE_URL, post_data.get('main'))
                or self._html_search_meta(['og:image', 'image'], webpage, 'thumbnail', fatal=False)),
            'timestamp': float_or_none(dict_get(post_data, ['cdate', 'udate']), scale=1000),
            'duration': float_or_none(post_data.get('vid_dur')),
            'tags': post_data.get('htgs'),
        }