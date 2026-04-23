def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        self._update_bid_tags(webpage, video_id)

        next_props = self._search_nextjs_data(webpage, video_id)['props']
        page_data = next_props['initialState']['play']
        video_info = page_data['curVideoInfo']

        uid = traverse_obj(
            self._parse_json(
                self._get_cookie('I00002', '{}'), video_id, transform_source=urllib.parse.unquote, fatal=False),
            ('data', 'uid'), default=0)

        if uid:
            vip_data = self._download_json(
                'https://pcw-api.iq.com/api/vtype', video_id, note='Downloading VIP data', errnote='Unable to download VIP data', query={
                    'batch': 1,
                    'platformId': 3,
                    'modeCode': self._get_cookie('mod', 'intl'),
                    'langCode': self._get_cookie('lang', 'en_us'),
                    'deviceId': self._get_cookie('QC005', ''),
                }, fatal=False)
            ut_list = traverse_obj(vip_data, ('data', 'all_vip', ..., 'vipType'), expected_type=str_or_none)
        else:
            ut_list = ['0']

        # bid 0 as an initial format checker
        dash_paths = self._parse_json(PhantomJSwrapper(self, timeout=120_000).get(
            url, note2='Executing signature code (this may take a couple minutes)',
            html='<!DOCTYPE html>', video_id=video_id, jscode=self._DASH_JS % {
                'tvid': video_info['tvId'],
                'vid': video_info['vid'],
                'src': traverse_obj(next_props, ('initialProps', 'pageProps', 'ptid'),
                                    expected_type=str, default='04022001010011000000'),
                'uid': uid,
                'dfp': self._get_cookie('dfp', ''),
                'mode': self._get_cookie('mod', 'intl'),
                'lang': self._get_cookie('lang', 'en_us'),
                'bid_list': '[' + ','.join(['0', *self._BID_TAGS.keys()]) + ']',
                'ut_list': '[' + ','.join(ut_list) + ']',
                'cmd5x_func': self._extract_cmd5x_function(webpage, video_id),
            })[1].strip(), video_id)

        formats, subtitles = [], {}
        initial_format_data = self._download_json(
            urljoin('https://cache-video.iq.com', dash_paths['0']), video_id,
            note='Downloading initial video format info', errnote='Unable to download initial video format info')['data']

        preview_time = traverse_obj(
            initial_format_data, ('boss_ts', (None, 'data'), ('previewTime', 'rtime')), expected_type=float_or_none, get_all=False)
        if traverse_obj(initial_format_data, ('boss_ts', 'data', 'prv'), expected_type=int_or_none):
            self.report_warning('This preview video is limited{}'.format(format_field(preview_time, None, ' to %s seconds')))

        # TODO: Extract audio-only formats
        for bid in set(traverse_obj(initial_format_data, ('program', 'video', ..., 'bid'), expected_type=str_or_none)):
            dash_path = dash_paths.get(bid)
            if not dash_path:
                self.report_warning(f'Unknown format id: {bid}. It is currently not being extracted')
                continue
            format_data = traverse_obj(self._download_json(
                urljoin('https://cache-video.iq.com', dash_path), video_id,
                note=f'Downloading format data for {self._BID_TAGS[bid]}', errnote='Unable to download format data',
                fatal=False), 'data', expected_type=dict)

            video_format = traverse_obj(format_data, ('program', 'video', lambda _, v: str(v['bid']) == bid),
                                        expected_type=dict, get_all=False) or {}
            extracted_formats = []
            if video_format.get('m3u8Url'):
                extracted_formats.extend(self._extract_m3u8_formats(
                    urljoin(format_data.get('dm3u8', 'https://cache-m.iq.com/dc/dt/'), video_format['m3u8Url']),
                    'mp4', m3u8_id=bid, fatal=False))
            if video_format.get('mpdUrl'):
                # TODO: Properly extract mpd hostname
                extracted_formats.extend(self._extract_mpd_formats(
                    urljoin(format_data.get('dm3u8', 'https://cache-m.iq.com/dc/dt/'), video_format['mpdUrl']),
                    mpd_id=bid, fatal=False))
            if video_format.get('m3u8'):
                ff = video_format.get('ff', 'ts')
                if ff == 'ts':
                    m3u8_formats, _ = self._parse_m3u8_formats_and_subtitles(
                        video_format['m3u8'], ext='mp4', m3u8_id=bid, fatal=False)
                    extracted_formats.extend(m3u8_formats)
                elif ff == 'm4s':
                    mpd_data = traverse_obj(
                        self._parse_json(video_format['m3u8'], video_id, fatal=False), ('payload', ..., 'data'), expected_type=str)
                    if not mpd_data:
                        continue
                    mpd_formats, _ = self._parse_mpd_formats_and_subtitles(
                        mpd_data, bid, format_data.get('dm3u8', 'https://cache-m.iq.com/dc/dt/'))
                    extracted_formats.extend(mpd_formats)
                else:
                    self.report_warning(f'{ff} formats are currently not supported')

            if not extracted_formats:
                if video_format.get('s'):
                    self.report_warning(f'{self._BID_TAGS[bid]} format is restricted')
                else:
                    self.report_warning(f'Unable to extract {self._BID_TAGS[bid]} format')
            for f in extracted_formats:
                f.update({
                    'quality': qualities(list(self._BID_TAGS.keys()))(bid),
                    'format_note': self._BID_TAGS[bid],
                    **parse_resolution(video_format.get('scrsz')),
                })
            formats.extend(extracted_formats)

        for sub_format in traverse_obj(initial_format_data, ('program', 'stl', ...), expected_type=dict):
            lang = self._LID_TAGS.get(str_or_none(sub_format.get('lid')), sub_format.get('_name'))
            subtitles.setdefault(lang, []).extend([{
                'ext': format_ext,
                'url': urljoin(initial_format_data.get('dstl', 'http://meta.video.iqiyi.com'), sub_format[format_key]),
            } for format_key, format_ext in [('srt', 'srt'), ('webvtt', 'vtt')] if sub_format.get(format_key)])

        extra_metadata = page_data.get('albumInfo') if video_info.get('albumId') and page_data.get('albumInfo') else video_info
        return {
            'id': video_id,
            'title': video_info['name'],
            'formats': formats,
            'subtitles': subtitles,
            'description': video_info.get('mergeDesc'),
            'duration': parse_duration(video_info.get('len')),
            'age_limit': parse_age_limit(video_info.get('rating')),
            'average_rating': traverse_obj(page_data, ('playScoreInfo', 'score'), expected_type=float_or_none),
            'timestamp': parse_iso8601(video_info.get('isoUploadDate')),
            'categories': traverse_obj(extra_metadata, ('videoTagMap', ..., ..., 'name'), expected_type=str),
            'cast': traverse_obj(extra_metadata, ('actorArr', ..., 'name'), expected_type=str),
            'episode_number': int_or_none(video_info.get('order')) or None,
            'series': video_info.get('albumName'),
        }