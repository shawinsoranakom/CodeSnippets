def _real_extract(self, url):
        host, video_id = self._match_valid_url(url).groups()
        content_info = try_get(
            self._call_api(
                host, f'content/{video_id}', video_id, note='Downloading content info API JSON'), lambda x: x['playerContentInfo'])
        # Fallback
        if not content_info:
            webpage = self._download_webpage(url, video_id)
            player_config = self._parse_json(
                self._search_regex(
                    r'config\s*=\s*({.+?})\s*;', webpage, 'mainstreaming player config',
                    default='{}', flags=re.DOTALL),
                video_id, transform_source=js_to_json, fatal=False) or {}
            content_info = player_config['contentInfo']

        host = content_info.get('host') or host
        video_id = content_info.get('contentID') or video_id
        title = content_info.get('title')
        description = traverse_obj(content_info, 'longDescription', 'shortDescription', expected_type=str)
        live_status = 'not_live'
        if content_info.get('drmEnabled'):
            self.report_drm(video_id)

        alternative_content_id = content_info.get('alternativeContentID')
        if alternative_content_id:
            self.report_warning(f'Ignoring alternative content ID: {alternative_content_id}')

        content_type = int_or_none(content_info.get('contentType'))
        format_base_url = None
        formats = []
        subtitles = {}
        # Live content
        if content_type == 20:
            dvr_enabled = traverse_obj(content_info, ('playerSettings', 'dvrEnabled'), expected_type=bool)
            format_base_url = f"https://{host}/live/{content_info['liveSourceID']}/{video_id}/%s{'?DVR' if dvr_enabled else ''}"
            live_status = 'is_live'
            heartbeat = self._call_api(host, f'heartbeat/{video_id}', video_id, note='Checking stream status') or {}
            if heartbeat.get('heartBeatUp') is False:
                self.raise_no_formats(f'MainStreaming said: {heartbeat.get("responseMessage")}', expected=True)
                live_status = 'was_live'

        # Playlist
        elif content_type == 31:
            return self.playlist_result(
                self._playlist_entries(host, content_info.get('playlistContents')), video_id, title, description)
        # Normal video content?
        elif content_type == 10:
            format_base_url = f'https://{host}/vod/{video_id}/%s'
            # Progressive format
            # Note: in https://webtools.msvdn.net/loader/playerV2.js there is mention of original.mp3 format,
            # however it seems to be the same as original.mp4?
            formats.append({'url': format_base_url % 'original.mp4', 'format_note': 'original', 'quality': 1})
        else:
            self.raise_no_formats(f'Unknown content type {content_type}')

        if format_base_url:
            m3u8_formats, m3u8_subs = self._extract_m3u8_formats_and_subtitles(
                format_base_url % 'playlist.m3u8', video_id=video_id, fatal=False)
            mpd_formats, mpd_subs = self._extract_mpd_formats_and_subtitles(
                format_base_url % 'manifest.mpd', video_id=video_id, fatal=False)

            subtitles = self._merge_subtitles(m3u8_subs, mpd_subs)
            formats.extend(m3u8_formats + mpd_formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'live_status': live_status,
            'duration': parse_duration(content_info.get('duration')),
            'tags': content_info.get('tags'),
            'subtitles': subtitles,
            'thumbnail': urljoin(self._get_webtools_base_url(host), f'image/{video_id}/poster'),
        }