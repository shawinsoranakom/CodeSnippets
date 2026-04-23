def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        duration = None
        formats = []

        player = self._parse_json(
            self._search_regex(
                r'Player\.init\s*\([^,]+,\s*({.+?})\s*,\s*{.+?}\s*\)\s*;',
                webpage, 'player', default='{}'), video_id, fatal=False)
        if player:
            for format_id, format_list in player['tracks'].items():
                if not isinstance(format_list, list):
                    format_list = [format_list]
                for format_dict in format_list:
                    if not isinstance(format_dict, dict):
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
            duration = int_or_none(player.get('duration'))
        else:
            # Old path, not actual as of 08.04.2020
            bitrates = self._parse_json(
                self._search_regex(
                    r'(?s)(?:src|bitrates)\s*=\s*({.+?})\s*;', webpage, 'formats'),
                video_id, transform_source=js_to_json)

            QUALITIES = ('lq', 'mq', 'hq', 'hd')
            quality_key = qualities(QUALITIES)

            for format_id, format_list in bitrates.items():
                if not isinstance(format_list, list):
                    format_list = [format_list]
                for format_url in format_list:
                    format_url = url_or_none(format_url)
                    if not format_url:
                        continue
                    if format_id == 'hls':
                        formats.extend(self._extract_m3u8_formats(
                            format_url, video_id, ext='mp4',
                            entry_protocol='m3u8_native', m3u8_id='hls',
                            fatal=False))
                        continue
                    f = {
                        'url': format_url,
                    }
                    f_id = format_id
                    for quality in QUALITIES:
                        if '%s.mp4' % quality in format_url:
                            f_id += '-%s' % quality
                            f.update({
                                'quality': quality_key(quality),
                                'format_note': quality.upper(),
                            })
                            break
                    f['format_id'] = f_id
                    formats.append(f)

        self._sort_formats(formats)

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