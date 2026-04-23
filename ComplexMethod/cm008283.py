def _real_extract(self, url):
        channel_id, msg_id = self._match_valid_url(url).group('channel_id', 'id')
        embed = self._download_webpage(
            url, msg_id, query={'embed': '1', 'single': []}, note='Downloading embed frame')

        def clean_text(html_class, html):
            text = clean_html(get_element_by_class(html_class, html))
            return text.replace('\n', ' ') if text else None

        description = clean_text('tgme_widget_message_text', embed)
        message = {
            'title': description or '',
            'description': description,
            'channel': clean_text('tgme_widget_message_author', embed),
            'channel_id': channel_id,
            'timestamp': unified_timestamp(self._search_regex(
                r'<time[^>]*datetime="([^"]*)"', embed, 'timestamp', fatal=False)),
        }

        videos = []
        for video in re.findall(r'<a class="tgme_widget_message_video_player(?s:.+?)</time>', embed):
            video_url = self._search_regex(
                r'<video[^>]+src="([^"]+)"', video, 'video URL', fatal=False)
            webpage_url = self._search_regex(
                r'<a class="tgme_widget_message_video_player[^>]+href="([^"]+)"',
                video, 'webpage URL', fatal=False)
            if not video_url or not webpage_url:
                continue
            formats = [{
                'url': video_url,
                'ext': 'mp4',
            }]
            videos.append({
                'id': url_basename(webpage_url),
                'webpage_url': update_url_query(webpage_url, {'single': True}),
                'duration': parse_duration(self._search_regex(
                    r'<time[^>]+duration[^>]*>([\d:]+)</time>', video, 'duration', fatal=False)),
                'thumbnail': self._search_regex(
                    r'tgme_widget_message_video_thumb"[^>]+background-image:url\(\'([^\']+)\'\)',
                    video, 'thumbnail', fatal=False),
                'formats': formats,
                **message,
            })

        playlist_id = None
        if len(videos) > 1 and 'single' not in parse_qs(url, keep_blank_values=True):
            playlist_id = f'{channel_id}-{msg_id}'

        if self._yes_playlist(playlist_id, msg_id):
            return self.playlist_result(
                videos, playlist_id, format_field(message, 'channel', f'%s {msg_id}'), description)
        else:
            return traverse_obj(videos, lambda _, x: x['id'] == msg_id, get_all=False)