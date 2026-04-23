def _real_extract(self, url):
        video_id, prefix = self._match_valid_url(url).group('id', 'prefix')
        headers = self.geo_verification_headers()
        webpage, urlh = self._download_webpage_handle(url, video_id, headers=headers)
        if not self._match_valid_url(urlh.url):
            return self.url_result(urlh.url)

        headers['Referer'] = url

        initial_state = self._search_json(r'window\.__INITIAL_STATE__\s*=', webpage, 'initial state', video_id, default=None)
        if not initial_state:
            if self._search_json(r'\bwindow\._riskdata_\s*=', webpage, 'risk', video_id, default={}).get('v_voucher'):
                raise ExtractorError('You have exceeded the rate limit. Try again later', expected=True)
            query = {'platform': 'web'}
            prefix = prefix.upper()
            if prefix == 'BV':
                query['bvid'] = prefix + video_id
            elif prefix == 'AV':
                query['aid'] = video_id
            detail = self._download_json(
                'https://api.bilibili.com/x/web-interface/wbi/view/detail', video_id,
                note='Downloading redirection URL', errnote='Failed to download redirection URL',
                query=self._sign_wbi(query, video_id), headers=headers)
            new_url = traverse_obj(detail, ('data', 'View', 'redirect_url', {url_or_none}))
            if new_url and BiliBiliBangumiIE.suitable(new_url):
                return self.url_result(new_url, BiliBiliBangumiIE)
            raise ExtractorError('Unable to extract initial state')

        if traverse_obj(initial_state, ('error', 'trueCode')) == -403:
            self.raise_login_required()
        if traverse_obj(initial_state, ('error', 'trueCode')) == -404:
            raise ExtractorError(
                'This video may be deleted or geo-restricted. '
                'You might want to try a VPN or a proxy server (with --proxy)', expected=True)

        is_festival = 'videoData' not in initial_state
        if is_festival:
            video_data = initial_state['videoInfo']
        else:
            video_data = initial_state['videoData']

        video_id, title = video_data['bvid'], video_data.get('title')

        # Bilibili anthologies are similar to playlists but all videos share the same video ID as the anthology itself.
        page_list_json = (not is_festival and traverse_obj(
            self._download_json(
                'https://api.bilibili.com/x/player/pagelist', video_id,
                fatal=False, query={'bvid': video_id, 'jsonp': 'jsonp'},
                note='Extracting videos in anthology', headers=headers),
            'data', expected_type=list)) or []
        is_anthology = len(page_list_json) > 1

        part_id = int_or_none(parse_qs(url).get('p', [None])[-1])
        if is_anthology and not part_id and self._yes_playlist(video_id, video_id):
            return self.playlist_from_matches(
                page_list_json, video_id, title, ie=BiliBiliIE,
                getter=lambda entry: f'https://www.bilibili.com/video/{video_id}?p={entry["page"]}')

        if is_anthology:
            part_id = part_id or 1
            title += f' p{part_id:02d} {traverse_obj(page_list_json, (part_id - 1, "part")) or ""}'

        aid = video_data.get('aid')
        old_video_id = format_field(aid, None, f'%s_part{part_id or 1}')
        cid = traverse_obj(video_data, ('pages', part_id - 1, 'cid')) if part_id else video_data.get('cid')

        festival_info = {}
        if is_festival:
            festival_info = traverse_obj(initial_state, {
                'uploader': ('videoInfo', 'upName'),
                'uploader_id': ('videoInfo', 'upMid', {str_or_none}),
                'like_count': ('videoStatus', 'like', {int_or_none}),
                'thumbnail': ('sectionEpisodes', lambda _, v: v['bvid'] == video_id, 'cover'),
            }, get_all=False)

        metainfo = {
            **traverse_obj(initial_state, {
                'uploader': ('upData', 'name'),
                'uploader_id': ('upData', 'mid', {str_or_none}),
                'like_count': ('videoData', 'stat', 'like', {int_or_none}),
                'tags': ('tags', ..., 'tag_name'),
                'thumbnail': ('videoData', 'pic', {url_or_none}),
            }),
            **festival_info,
            **traverse_obj(video_data, {
                'description': 'desc',
                'timestamp': ('pubdate', {int_or_none}),
                'view_count': (('viewCount', ('stat', 'view')), {int_or_none}),
                'comment_count': ('stat', 'reply', {int_or_none}),
            }, get_all=False),
            'id': f'{video_id}{format_field(part_id, None, "_p%d")}',
            '_old_archive_ids': [make_archive_id(self, old_video_id)] if old_video_id else None,
            'title': title,
            'http_headers': {'Referer': url},
        }

        is_interactive = traverse_obj(video_data, ('rights', 'is_stein_gate'))
        if is_interactive:
            return self.playlist_result(
                self._get_interactive_entries(video_id, cid, metainfo, headers=headers), **metainfo,
                duration=traverse_obj(initial_state, ('videoData', 'duration', {int_or_none})),
                __post_extractor=self.extract_comments(aid))

        play_info = None
        if self.is_logged_in:
            play_info = traverse_obj(
                self._search_json(r'window\.__playinfo__\s*=', webpage, 'play info', video_id, default=None),
                ('data', {dict}))
        if not play_info:
            play_info = self._download_playinfo(video_id, cid, headers=headers, query={'try_look': 1})
        formats = self.extract_formats(play_info)

        if video_data.get('is_upower_exclusive'):
            high_level = traverse_obj(initial_state, ('elecFullInfo', 'show_info', 'high_level', {dict})) or {}
            msg = f'{join_nonempty("title", "sub_title", from_dict=high_level, delim="，")}. {self._login_hint()}'
            if not formats:
                raise ExtractorError(f'This is a supporter-only video: {msg}', expected=True)
            if '试看' in traverse_obj(play_info, ('accept_description', ..., {str})):
                self.report_warning(
                    f'This is a supporter-only video, only the preview will be extracted: {msg}',
                    video_id=video_id)

        if not traverse_obj(play_info, 'dash'):
            # we only have legacy formats and need additional work
            has_qn = lambda x: x in traverse_obj(formats, (..., 'quality'))
            for qn in traverse_obj(play_info, ('accept_quality', lambda _, v: not has_qn(v), {int})):
                formats.extend(traverse_obj(
                    self.extract_formats(self._download_playinfo(video_id, cid, headers=headers, query={'qn': qn})),
                    lambda _, v: not has_qn(v['quality'])))
            self._check_missing_formats(play_info, formats)
            flv_formats = traverse_obj(formats, lambda _, v: v['fragments'])
            if flv_formats and len(flv_formats) < len(formats):
                # Flv and mp4 are incompatible due to `multi_video` workaround, so drop one
                if not self._configuration_arg('prefer_multi_flv'):
                    dropped_fmts = ', '.join(
                        f'{f.get("format_note")} ({f.get("format_id")})' for f in flv_formats)
                    formats = traverse_obj(formats, lambda _, v: not v.get('fragments'))
                    if dropped_fmts:
                        self.to_screen(
                            f'Dropping incompatible flv format(s) {dropped_fmts} since mp4 is available. '
                            'To extract flv, pass --extractor-args "bilibili:prefer_multi_flv"')
                else:
                    formats = traverse_obj(
                        # XXX: Filtering by extractor-arg is for testing purposes
                        formats, lambda _, v: v['quality'] == int(self._configuration_arg('prefer_multi_flv')[0]),
                    ) or [max(flv_formats, key=lambda x: x['quality'])]

        if traverse_obj(formats, (0, 'fragments')):
            # We have flv formats, which are individual short videos with their own timestamps and metainfo
            # Binary concatenation corrupts their timestamps, so we need a `multi_video` workaround
            return {
                **metainfo,
                '_type': 'multi_video',
                'entries': [{
                    'id': f'{metainfo["id"]}_{idx}',
                    'title': metainfo['title'],
                    'http_headers': metainfo['http_headers'],
                    'formats': [{
                        **fragment,
                        'format_id': formats[0].get('format_id'),
                    }],
                    'subtitles': self.extract_subtitles(video_id, cid) if idx == 0 else None,
                    '__post_extractor': self.extract_comments(aid) if idx == 0 else None,
                } for idx, fragment in enumerate(formats[0]['fragments'])],
                'duration': float_or_none(play_info.get('timelength'), scale=1000),
            }

        return {
            **metainfo,
            'formats': formats,
            'duration': float_or_none(play_info.get('timelength'), scale=1000),
            'chapters': self._get_chapters(aid, cid),
            'subtitles': self.extract_subtitles(video_id, cid),
            '__post_extractor': self.extract_comments(aid),
        }