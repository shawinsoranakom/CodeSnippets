def _real_extract(self, url):
        channel_name = self._match_id(url).lower()

        gql = self._download_gql(
            channel_name, [{
                'operationName': 'StreamMetadata',
                'variables': {
                    'channelLogin': channel_name,
                    'includeIsDJ': True,
                },
            }, {
                'operationName': 'ComscoreStreamingQuery',
                'variables': {
                    'channel': channel_name,
                    'clipSlug': '',
                    'isClip': False,
                    'isLive': True,
                    'isVodOrCollection': False,
                    'vodID': '',
                },
            }, {
                'operationName': 'VideoPreviewOverlay',
                'variables': {'login': channel_name},
            }],
            'Downloading stream GraphQL')

        user = gql[0]['data']['user']

        if not user:
            raise ExtractorError(
                f'{channel_name} does not exist', expected=True)

        stream = user['stream']

        if not stream:
            raise UserNotLive(video_id=channel_name)

        timestamp = unified_timestamp(stream.get('createdAt'))

        if self.get_param('live_from_start'):
            self.to_screen(f'{channel_name}: Extracting VOD to download live from start')
            entry = next(self._entries(channel_name, None, 'time'), None)
            if entry and entry.pop('timestamp') >= (timestamp or float('inf')):
                return entry
            self.report_warning(
                'Unable to extract the VOD associated with this livestream', video_id=channel_name)

        access_token = self._download_access_token(
            channel_name, 'stream', 'channelName')

        stream_id = stream.get('id') or channel_name
        formats = self._extract_twitch_m3u8_formats(
            'api/channel/hls', channel_name, access_token['value'], access_token['signature'])
        self._prefer_source(formats)

        view_count = stream.get('viewers')

        sq_user = try_get(gql, lambda x: x[1]['data']['user'], dict) or {}
        uploader = sq_user.get('displayName')
        description = try_get(
            sq_user, lambda x: x['broadcastSettings']['title'], str)

        thumbnail = url_or_none(try_get(
            gql, lambda x: x[2]['data']['user']['stream']['previewImageURL'],
            str))

        title = uploader or channel_name
        stream_type = stream.get('type')
        if stream_type in ['rerun', 'live']:
            title += f' ({stream_type})'

        return {
            'id': stream_id,
            'display_id': channel_name,
            'title': title,
            'description': description,
            'thumbnails': self._get_thumbnails(thumbnail),
            'uploader': uploader,
            'uploader_id': channel_name,
            'timestamp': timestamp,
            'view_count': view_count,
            'formats': formats,
            'is_live': stream_type == 'live',
        }