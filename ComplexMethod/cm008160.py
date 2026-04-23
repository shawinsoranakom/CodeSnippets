def _real_extract(self, url):
        post_id = self._match_id(url)

        post_data = self._download_json(
            f'{self._BASE_URL}/api/v3/content/post', post_id, query={'id': post_id},
            note='Downloading post data', errnote='Unable to download post data',
            impersonate=self._IMPERSONATE_TARGET)

        if not any(traverse_obj(post_data, ('metadata', ('hasVideo', 'hasAudio')))):
            raise ExtractorError('Post does not contain a video or audio track', expected=True)

        uploader_url = format_field(
            post_data, [('creator', 'urlname')], f'{self._BASE_URL}/channel/%s/home') or None

        common_info = {
            'uploader_url': uploader_url,
            'channel_url': urljoin(f'{uploader_url}/', traverse_obj(post_data, ('channel', 'urlname'))),
            'availability': self._availability(needs_subscription=True),
            **traverse_obj(post_data, {
                'uploader': ('creator', 'title', {str}),
                'uploader_id': ('creator', 'id', {str}),
                'channel': ('channel', 'title', {str}),
                'channel_id': ('channel', 'id', {str}),
                'release_timestamp': ('releaseDate', {parse_iso8601}),
            }),
        }

        items = []
        for media in traverse_obj(post_data, (('videoAttachments', 'audioAttachments'), ...)):
            media_id = media['id']
            media_typ = media.get('type') or 'video'

            stream = self._download_json(
                f'{self._BASE_URL}/api/v3/delivery/info', media_id,
                query={'scenario': 'onDemand', 'entityId': media_id},
                note=f'Downloading {media_typ} stream data',
                impersonate=self._IMPERSONATE_TARGET)

            metadata = self._download_json(
                f'{self._BASE_URL}/api/v3/content/{media_typ}', media_id,
                f'Downloading {media_typ} metadata', query={'id': media_id},
                fatal=False, impersonate=self._IMPERSONATE_TARGET)

            cdn_base_url = traverse_obj(stream, (
                'groups', 0, 'origins', ..., 'url', {url_or_none}, any, {require('cdn base url')}))

            formats = []
            for variant in traverse_obj(stream, ('groups', 0, 'variants', lambda _, v: v['url'])):
                format_url = urljoin(cdn_base_url, variant['url'])
                format_id = traverse_obj(variant, ('name', {str}))
                hls_aes = {}
                m3u8_data = None

                # If we need impersonation for the API, then we need it for HLS keys too: extract in advance
                if self._IMPERSONATE_TARGET is not None:
                    m3u8_data = self._download_webpage(
                        format_url, media_id, fatal=False, impersonate=self._IMPERSONATE_TARGET, headers=self._HEADERS,
                        note=join_nonempty('Downloading', format_id, 'm3u8 information', delim=' '),
                        errnote=join_nonempty('Failed to download', format_id, 'm3u8 information', delim=' '))
                    if not m3u8_data:
                        continue

                    key_url = self._search_regex(
                        r'#EXT-X-KEY:METHOD=AES-128,URI="(https?://[^"]+)"',
                        m3u8_data, 'HLS AES key URI', default=None)
                    if key_url:
                        urlh = self._request_webpage(
                            key_url, media_id, fatal=False, impersonate=self._IMPERSONATE_TARGET, headers=self._HEADERS,
                            note=join_nonempty('Downloading', format_id, 'HLS AES key', delim=' '),
                            errnote=join_nonempty('Failed to download', format_id, 'HLS AES key', delim=' '))
                        if urlh:
                            hls_aes['key'] = urlh.read().hex()

                formats.append({
                    **traverse_obj(variant, {
                        'format_note': ('label', {str}),
                        'width': ('meta', 'video', 'width', {int_or_none}),
                        'height': ('meta', 'video', 'height', {int_or_none}),
                        'vcodec': ('meta', 'video', 'codec', {str}),
                        'acodec': ('meta', 'audio', 'codec', {str}),
                        'vbr': ('meta', 'video', 'bitrate', 'average', {int_or_none(scale=1000)}),
                        'abr': ('meta', 'audio', 'bitrate', 'average', {int_or_none(scale=1000)}),
                        'audio_channels': ('meta', 'audio', 'channelCount', {int_or_none}),
                        'fps': ('meta', 'video', 'fps', {float_or_none}),
                    }),
                    'url': format_url,
                    'ext': determine_ext(format_url.partition('/chunk.m3u8')[0], 'mp4'),
                    'format_id': format_id,
                    'hls_media_playlist_data': m3u8_data,
                    'hls_aes': hls_aes or None,
                })

            subtitles = {}
            automatic_captions = {}
            for sub_data in traverse_obj(metadata, ('textTracks', lambda _, v: url_or_none(v['src']))):
                sub_lang = sub_data.get('language') or 'en'
                sub_entry = {'url': sub_data['src']}
                if sub_data.get('generated'):
                    automatic_captions.setdefault(sub_lang, []).append(sub_entry)
                else:
                    subtitles.setdefault(sub_lang, []).append(sub_entry)

            items.append({
                **common_info,
                'id': media_id,
                **traverse_obj(metadata, {
                    'title': ('title', {str}),
                    'duration': ('duration', {int_or_none}),
                    'thumbnail': ('thumbnail', 'path', {url_or_none}),
                }),
                'formats': formats,
                'subtitles': subtitles,
                'automatic_captions': automatic_captions,
            })

        post_info = {
            **common_info,
            'id': post_id,
            'display_id': post_id,
            **traverse_obj(post_data, {
                'title': ('title', {str}),
                'description': ('text', {clean_html}),
                'like_count': ('likes', {int_or_none}),
                'dislike_count': ('dislikes', {int_or_none}),
                'comment_count': ('comments', {int_or_none}),
                'thumbnail': ('thumbnail', 'path', {url_or_none}),
            }),
            'http_headers': self._HEADERS,
        }

        if len(items) > 1:
            return self.playlist_result(items, **post_info)

        post_info.update(items[0])
        return post_info