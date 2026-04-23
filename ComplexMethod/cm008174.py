def _real_extract(self, url):
        vid = self._match_id(url)

        # NOTE: It is also possible to extract this info from the Nuxt data on the website,
        # however that seems unreliable - sometimes it randomly doesn't return the data,
        # at least when using a non-residential IP.
        resp = self._call_api(vid, data={
            'operationName': 'vod_VodReaderService_BatchGetVodDetailInfo',
            'variables': {
                'params': {
                    'vids': [vid],
                },
            },
            'extensions': {},
        })

        vod_detail_info = traverse_obj(resp, ('VodDetailInfos', vid), expected_type=dict)
        if not vod_detail_info:
            raise ExtractorError('This video not found or not available anymore', expected=True)
        vod_info = vod_detail_info.get('vodInfo')
        title = vod_info.get('title')

        if try_get(vod_info, lambda x: x['playbackRights']['playbackRights'] != 'Normal'):
            playback_rights_setting = vod_info['playbackRights']['playbackRightsSetting']
            if playback_rights_setting == 'SubscriberOnly':
                raise ExtractorError('This video is only available for subscribers', expected=True)
            else:
                raise ExtractorError(f'This video is not available ({playback_rights_setting})', expected=True)

        language = vod_info.get('languageName')
        formats = []
        for play_info in (vod_info.get('playInfos') or []):
            play_url = play_info.get('playUrl')
            if not play_url:
                continue
            format_id = play_info.get('desc')
            formats.append({
                'ext': 'mp4',
                'filesize': int_or_none(play_info.get('fileSize')),
                'format_id': format_id,
                'height': int_or_none(format_id[:-1]) if format_id else None,
                'language': language,
                'protocol': 'm3u8_native',
                'tbr': int_or_none(play_info.get('bitrate')),
                'url': play_url,
                'http_headers': self._HEADERS,
            })

        category = vod_info.get('categoryName')
        get_count = lambda x: int_or_none(vod_info.get(x + 'Num'))

        info = {
            'id': vid,
            'title': title,
            'formats': formats,
            'thumbnail': vod_info.get('coverUrl'),
            'timestamp': int_or_none(vod_info.get('publishTs')),
            'duration': int_or_none(vod_info.get('duration')),
            'view_count': get_count('watch'),
            'like_count': get_count('like'),
            'comment_count': get_count('comment'),
            'categories': [category] if category else None,
            '__post_extractor': self.extract_comments(vid),
        }
        info.update(self._extract_streamer_info(vod_detail_info))
        return info