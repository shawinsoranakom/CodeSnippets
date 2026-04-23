def _extract_formats(self, cid, video_id, record_id=None, is_live=False):
        postdata_common = {
            'https_watch_urls': True,
        }

        if is_live:
            postdata_common.update({'timeshift': 10800})
            url = '%s/zapi/watch/live/%s' % (self._host_url(), cid)
        elif record_id:
            url = '%s/zapi/watch/recording/%s' % (self._host_url(), record_id)
        else:
            url = '%s/zapi/watch/recall/%s/%s' % (self._host_url(), cid, video_id)

        formats = []
        for stream_type in ('dash', 'hls', 'hls5', 'hds'):
            postdata = postdata_common.copy()
            postdata['stream_type'] = stream_type

            data = self._download_json(
                url, video_id, 'Downloading %s formats' % stream_type.upper(),
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
                format_id_list = [stream_type]
                maxrate = watch.get('maxrate')
                if maxrate:
                    format_id_list.append(compat_str(maxrate))
                audio_channel = watch.get('audio_channel')
                if audio_channel:
                    format_id_list.append(compat_str(audio_channel))
                preference = 1 if audio_channel == 'A' else None
                format_id = '-'.join(format_id_list)
                if stream_type in ('dash', 'dash_widevine', 'dash_playready'):
                    this_formats = self._extract_mpd_formats(
                        watch_url, video_id, mpd_id=format_id, fatal=False)
                elif stream_type in ('hls', 'hls5', 'hls5_fairplay'):
                    this_formats = self._extract_m3u8_formats(
                        watch_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id=format_id,
                        fatal=False)
                elif stream_type == 'hds':
                    this_formats = self._extract_f4m_formats(
                        watch_url, video_id, f4m_id=format_id, fatal=False)
                elif stream_type == 'smooth_playready':
                    this_formats = self._extract_ism_formats(
                        watch_url, video_id, ism_id=format_id, fatal=False)
                else:
                    assert False
                for this_format in this_formats:
                    this_format['preference'] = preference
                formats.extend(this_formats)
        self._sort_formats(formats)
        return formats