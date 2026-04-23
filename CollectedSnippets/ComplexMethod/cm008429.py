def _extract_formats(self, cid, video_id, record_id=None, ondemand_id=None, ondemand_termtoken=None, ondemand_type=None, is_live=False):
        postdata_common = {
            'https_watch_urls': True,
        }

        if is_live:
            postdata_common.update({'timeshift': 10800})
            url = f'{self._host_url()}/zapi/watch/live/{cid}'
        elif record_id:
            url = f'{self._host_url()}/zapi/watch/recording/{record_id}'
        elif ondemand_id:
            postdata_common.update({
                'teasable_id': ondemand_id,
                'term_token': ondemand_termtoken,
                'teasable_type': ondemand_type,
            })
            url = f'{self._host_url()}/zapi/watch/vod/video'
        else:
            url = f'{self._host_url()}/zapi/v3/watch/replay/{cid}/{video_id}'
        formats = []
        subtitles = {}
        for stream_type in ('dash', 'hls7'):
            postdata = postdata_common.copy()
            postdata['stream_type'] = stream_type

            data = self._download_json(
                url, video_id, f'Downloading {stream_type.upper()} formats',
                data=urlencode_postdata(postdata), fatal=False)
            if not data:
                continue

            watch_urls = try_get(
                data, lambda x: x['stream']['watch_urls'], list)
            if not watch_urls:
                continue

            for watch in watch_urls:
                if not isinstance(watch, dict):
                    continue
                watch_url = url_or_none(watch.get('url'))
                if not watch_url:
                    continue
                audio_channel = watch.get('audio_channel')
                preference = 1 if audio_channel == 'A' else None
                format_id = join_nonempty(stream_type, watch.get('maxrate'), audio_channel)
                if stream_type.startswith('dash'):
                    this_formats, subs = self._extract_mpd_formats_and_subtitles(
                        watch_url, video_id, mpd_id=format_id, fatal=False)
                    self._merge_subtitles(subs, target=subtitles)
                elif stream_type.startswith('hls'):
                    this_formats, subs = self._extract_m3u8_formats_and_subtitles(
                        watch_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id=format_id,
                        fatal=False)
                    self._merge_subtitles(subs, target=subtitles)
                elif stream_type == 'hds':
                    this_formats = self._extract_f4m_formats(
                        watch_url, video_id, f4m_id=format_id, fatal=False)
                elif stream_type == 'smooth_playready':
                    this_formats = self._extract_ism_formats(
                        watch_url, video_id, ism_id=format_id, fatal=False)
                else:
                    assert False
                for this_format in this_formats:
                    this_format['quality'] = preference
                formats.extend(this_formats)
        return formats, subtitles