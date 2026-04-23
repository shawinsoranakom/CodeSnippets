def _real_extract(self, url):
        channel_id = self._match_id(url)
        live_detail = self._download_json(
            f'https://api.chzzk.naver.com/service/v3/channels/{channel_id}/live-detail', channel_id,
            note='Downloading channel info', errnote='Unable to download channel info')['content']

        if live_detail.get('status') == 'CLOSE':
            raise UserNotLive(video_id=channel_id)

        live_playback = self._parse_json(live_detail['livePlaybackJson'], channel_id)

        thumbnails = []
        thumbnail_template = traverse_obj(
            live_playback, ('thumbnail', 'snapshotThumbnailTemplate', {url_or_none}))
        if thumbnail_template and '{type}' in thumbnail_template:
            for width in traverse_obj(live_playback, ('thumbnail', 'types', ..., {str})):
                thumbnails.append({
                    'id': width,
                    'url': thumbnail_template.replace('{type}', width),
                    'width': int_or_none(width),
                })

        formats, subtitles = [], {}
        for media in traverse_obj(live_playback, ('media', lambda _, v: url_or_none(v['path']))):
            is_low_latency = media.get('mediaId') == 'LLHLS'
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                media['path'], channel_id, 'mp4', fatal=False, live=True,
                m3u8_id='hls-ll' if is_low_latency else 'hls')
            for f in fmts:
                if is_low_latency:
                    f['source_preference'] = -2
                if '-afragalow.stream-audio.stream' in f['format_id']:
                    f['quality'] = -2
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return {
            'id': channel_id,
            'is_live': True,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            **traverse_obj(live_detail, {
                'title': ('liveTitle', {str}),
                'timestamp': ('openDate', {parse_iso8601(delimiter=' ')}),
                'concurrent_view_count': ('concurrentUserCount', {int_or_none}),
                'view_count': ('accumulateCount', {int_or_none}),
                'channel': ('channel', 'channelName', {str}),
                'channel_id': ('channel', 'channelId', {str}),
                'channel_is_verified': ('channel', 'verifiedMark', {bool}),
            }),
        }