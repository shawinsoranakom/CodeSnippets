def _extract_episode_info(self, url, episode=None):
        fetch_episode = episode is None
        lang, m_type, episode_id = NhkVodIE._match_valid_url(url).group('lang', 'type', 'id')
        is_video = m_type != 'audio'

        if fetch_episode:
            episode = self._call_api(
                episode_id, lang, is_video, is_episode=True, is_clip=episode_id[:4] == '9999')

        video_id = join_nonempty('id', 'lang', from_dict=episode)

        title = episode.get('title')
        series = traverse_obj(episode, (('video_program', 'audio_program'), any, 'title'))

        episode_name = title
        if series and title:
            title = f'{series} - {title}'
        elif series and not title:
            title = series
            series = None
            episode_name = None
        else:  # title, no series
            episode_name = None

        info = {
            'id': video_id,
            'title': title,
            'series': series,
            'episode': episode_name,
            **traverse_obj(episode, {
                'description': ('description', {str}),
                'release_timestamp': ('first_broadcasted_at', {unified_timestamp}),
                'categories': ('categories', ..., 'name', {str}),
                'tags': ('tags', ..., 'name', {str}),
                'thumbnails': ('images', lambda _, v: v['url'], {
                    'url': ('url', {urljoin(url)}),
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                }),
                'webpage_url': ('url', {urljoin(url)}),
            }),
            'extractor_key': NhkVodIE.ie_key(),
            'extractor': NhkVodIE.IE_NAME,
        }

        # XXX: We are assuming that 'video' and 'audio' are mutually exclusive
        stream_info = traverse_obj(episode, (('video', 'audio'), {dict}, any)) or {}
        if not stream_info.get('url'):
            self.raise_no_formats('Stream not found; it has most likely expired', expected=True)
        else:
            stream_url = stream_info['url']
            if is_video:
                formats, subtitles = self._extract_m3u8_formats_and_subtitles(stream_url, video_id)
                info.update({
                    'formats': formats,
                    'subtitles': subtitles,
                    **traverse_obj(stream_info, ({
                        'duration': ('duration', {int_or_none}),
                        'timestamp': ('published_at', {unified_timestamp}),
                    })),
                })
            else:
                # From https://www3.nhk.or.jp/nhkworld/common/player/radio/inline/rod.html
                audio_path = remove_end(stream_url, '.m4a')
                info['formats'] = self._extract_m3u8_formats(
                    f'{urljoin("https://vod-stream.nhk.jp", audio_path)}/index.m3u8',
                    episode_id, 'm4a', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False)
                for f in info['formats']:
                    f['language'] = lang

        return info