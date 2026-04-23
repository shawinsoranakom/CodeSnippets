def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'https://vbox7.com/play:%s' % (video_id,)

        now = time.time()
        response = self._download_json(
            'https://www.vbox7.com/aj/player/item/options', video_id,
            query={'vid': video_id}, headers={'Referer': url})
        # estimate time to which possible `ago` member is relative
        now = now + 0.5 * (time.time() - now)

        if traverse_obj(response, 'error'):
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, response['error']), expected=True)

        src_url = traverse_obj(response, ('options', 'src', T(url_or_none))) or ''

        fmt_base = url_basename(src_url).rsplit('.', 1)[0].rsplit('_', 1)[0]
        if fmt_base in ('na', 'vn'):
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        ext = determine_ext(src_url)
        if ext == 'mpd':
            # extract MPD
            try:
                formats, subtitles = self._extract_mpd_formats_and_subtitles(
                    src_url, video_id, 'dash', fatal=False)
            except KeyError:  # fatal doesn't catch this
                self.report_warning('Failed to parse MPD manifest')
                formats, subtitles = [], {}
        elif ext != 'm3u8':
            formats = [{
                'url': src_url,
            }] if src_url else []
            subtitles = {}

        if src_url:
            # possibly extract HLS, based on https://github.com/yt-dlp/yt-dlp/pull/9100
            fmt_base = base_url(src_url) + fmt_base
            # prepare for _extract_m3u8_formats_and_subtitles()
            # hls_formats, hls_subs = self._extract_m3u8_formats_and_subtitles(
            hls_formats = self._extract_m3u8_formats(
                '{0}.m3u8'.format(fmt_base), video_id, m3u8_id='hls', fatal=False)
            formats.extend(hls_formats)
            # self._merge_subtitles(hls_subs, target=subtitles)

            # In case MPD/HLS cannot be parsed, or anyway, get mp4 combined
            # formats usually provided to Safari, iOS, and old Windows
            video = response['options']
            resolutions = (1080, 720, 480, 240, 144)
            highest_res = traverse_obj(video, (
                'highestRes', T(int))) or resolutions[0]
            resolutions = traverse_obj(video, (
                'resolutions', lambda _, r: highest_res >= int(r) > 0)) or resolutions
            mp4_formats = traverse_obj(resolutions, (
                Ellipsis, T(lambda res: {
                    'url': '{0}_{1}.mp4'.format(fmt_base, res),
                    'format_id': 'http-{0}'.format(res),
                    'height': res,
                })))
            # if above formats are flaky, enable the line below
            # self._check_formats(mp4_formats, video_id)
            formats.extend(mp4_formats)

        self._sort_formats(formats)

        webpage = self._download_webpage(url, video_id, fatal=False) or ''

        info = self._search_json_ld(
            webpage.replace('"/*@context"', '"@context"'), video_id,
            fatal=False) if webpage else {}

        if not info.get('title'):
            info['title'] = traverse_obj(response, (
                'options', 'title', T(txt_or_none))) or self._og_search_title(webpage)

        def if_missing(k):
            return lambda x: None if k in info else x

        info = merge_dicts(info, {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles or None,
        }, info, traverse_obj(response, ('options', {
            'uploader': ('uploader', T(txt_or_none)),
            'timestamp': ('ago', T(if_missing('timestamp')), T(lambda t: int(round((now - t) / 60.0)) * 60)),
            'duration': ('duration', T(if_missing('duration')), T(float_or_none)),
        })))
        if 'thumbnail' not in info:
            info['thumbnail'] = self._proto_relative_url(
                info.get('thumbnail') or self._og_search_thumbnail(webpage),
                'https:'),

        return info