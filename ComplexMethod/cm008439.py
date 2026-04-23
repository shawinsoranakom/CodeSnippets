def _real_extract(self, url):
        broadcast_type, display_id = self._match_valid_url(url).group('type', 'id')

        if broadcast_type == 'events':
            timeline = self._call_api(
                f'live_event/1/{display_id}/timeline.json', display_id)
            broadcast_id = traverse_obj(timeline, (
                'twitter_objects', 'broadcasts', ..., ('id', 'broadcast_id'),
                {str}, any, {require('broadcast ID')}))
        else:
            broadcast_id = display_id

        broadcast = self._call_api(
            'broadcasts/show.json', broadcast_id,
            {'ids': broadcast_id})['broadcasts'][broadcast_id]
        if not broadcast:
            raise ExtractorError('Broadcast no longer exists', expected=True)
        info = self._parse_broadcast_data(broadcast, broadcast_id)
        info.update({
            'display_id': display_id,
            'title': broadcast.get('status') or info.get('title'),
            'uploader_id': broadcast.get('twitter_username') or info.get('uploader_id'),
            'uploader_url': format_field(
                broadcast, 'twitter_username', 'https://twitter.com/%s', default=None),
        })
        if info['live_status'] == 'is_upcoming':
            self.raise_no_formats('This live broadcast has not yet started', expected=True)
            return info

        media_key = broadcast['media_key']
        source = self._call_api(
            f'live_video_stream/status/{media_key}', media_key)['source']
        m3u8_url = source.get('noRedirectPlaybackUrl') or source['location']
        if '/live_video_stream/geoblocked/' in m3u8_url:
            self.raise_geo_restricted()
        m3u8_id = urllib.parse.parse_qs(urllib.parse.urlparse(
            m3u8_url).query).get('type', [None])[0]
        state, width, height = self._extract_common_format_info(broadcast)
        info['formats'] = self._extract_pscp_m3u8_formats(
            m3u8_url, broadcast_id, m3u8_id, state, width, height)
        return info