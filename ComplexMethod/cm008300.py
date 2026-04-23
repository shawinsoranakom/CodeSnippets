def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        has_drm = False
        duration = None
        formats = []

        def process_format_list(format_list, format_id=''):
            nonlocal formats, has_drm
            if not isinstance(format_list, list):
                format_list = [format_list]
            for format_dict in format_list:
                if not isinstance(format_dict, dict):
                    continue
                if (not self.get_param('allow_unplayable_formats')
                        and traverse_obj(format_dict, ('drm', 'keySystem'))):
                    has_drm = True
                    continue
                format_url = url_or_none(format_dict.get('src'))
                format_type = format_dict.get('type')
                ext = determine_ext(format_url)
                if (format_type == 'application/x-mpegURL'
                        or format_id == 'HLS' or ext == 'm3u8'):
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
                elif (format_type == 'application/dash+xml'
                      or format_id == 'DASH' or ext == 'mpd'):
                    formats.extend(self._extract_mpd_formats(
                        format_url, video_id, mpd_id='dash', fatal=False))
                else:
                    formats.append({
                        'url': format_url,
                    })

        player = self._search_json(
            r'player:', webpage, 'player', video_id, fatal=False, end_pattern=r';\s*</script>')
        if player:
            for src in traverse_obj(player, ('lib', 'source', 'sources', ...)):
                process_format_list(src)
            duration = traverse_obj(player, ('sourceInfo', 'duration', {int_or_none}))
        if not formats and not has_drm:
            # older code path, in use before August 2023
            player = self._parse_json(
                self._search_regex(
                    (r'(?:(?:replacePlaceholders|processAdTagModifier).*?:\s*)?(?:replacePlaceholders|processAdTagModifier)\s*\(\s*(?P<json>{.*?})\s*\)(?:\s*\))?\s*,',
                     r'Player\.init\s*\([^,]+,(?P<cndn>\s*\w+\s*\?)?\s*(?P<json>{(?(cndn).+?|.+)})\s*(?(cndn):|,\s*{.+?}\s*\)\s*;)'),
                    webpage, 'player', group='json'), video_id)
            if player:
                for format_id, format_list in player['tracks'].items():
                    process_format_list(format_list, format_id)
                duration = int_or_none(player.get('duration'))

        if not formats and has_drm:
            self.report_drm(video_id)

        title = self._og_search_title(
            webpage, default=None) or self._search_regex(
            (r'<value>(?P<title>[^<]+)',
             r'videoTitle\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1'), webpage,
            'title', group='value')
        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or self._search_regex(
            r'poster\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage,
            'thumbnail', fatal=False, group='value')
        duration = int_or_none(self._search_regex(
            r'videoDuration\s*:\s*(\d+)', webpage, 'duration',
            default=duration))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }