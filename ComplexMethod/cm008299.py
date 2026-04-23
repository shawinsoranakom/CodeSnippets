def _real_extract(self, url):
        slug, video_id = self._match_valid_url(url).group('slug', 'id')

        try:
            data = self._download_json(
                f'https://www.reddit.com/{slug}/.json', video_id, expected_status=403)
        except ExtractorError as e:
            if isinstance(e.cause, json.JSONDecodeError):
                if self._get_cookies('https://www.reddit.com/').get('reddit_session'):
                    raise ExtractorError('Your IP address is unable to access the Reddit API', expected=True)
                self.raise_login_required('Account authentication is required')
            raise

        if traverse_obj(data, 'error') == 403:
            reason = data.get('reason')
            if reason == 'quarantined':
                self.raise_login_required('Quarantined subreddit; an account that has opted in is required')
            elif reason == 'private':
                self.raise_login_required('Private subreddit; an account that has been approved is required')
            else:
                raise ExtractorError(f'HTTP Error 403 Forbidden; reason given: {reason}')

        data = data[0]['data']['children'][0]['data']
        video_url = data['url']

        thumbnails = []

        def add_thumbnail(src):
            if not isinstance(src, dict):
                return
            thumbnail_url = url_or_none(src.get('url'))
            if not thumbnail_url:
                return
            thumbnails.append({
                'url': unescapeHTML(thumbnail_url),
                'width': int_or_none(src.get('width')),
                'height': int_or_none(src.get('height')),
                'http_headers': {'Accept': '*/*'},
            })

        for image in try_get(data, lambda x: x['preview']['images']) or []:
            if not isinstance(image, dict):
                continue
            add_thumbnail(image.get('source'))
            resolutions = image.get('resolutions')
            if isinstance(resolutions, list):
                for resolution in resolutions:
                    add_thumbnail(resolution)

        info = {
            'thumbnails': thumbnails,
            'age_limit': {True: 18, False: 0}.get(data.get('over_18')),
            **traverse_obj(data, {
                'title': ('title', {truncate_string(left=72)}),
                'alt_title': ('title', {str}),
                'description': ('selftext', {str}, filter),
                'timestamp': ('created_utc', {float_or_none}),
                'uploader': ('author', {str}),
                'channel_id': ('subreddit', {str}),
                'like_count': ('ups', {int_or_none}),
                'dislike_count': ('downs', {int_or_none}),
                'comment_count': ('num_comments', {int_or_none}),
            }),
        }

        parsed_url = urllib.parse.urlparse(video_url)

        # Check for embeds in text posts, or else raise to avoid recursing into the same reddit URL
        if 'reddit.com' in parsed_url.netloc and f'/{video_id}/' in parsed_url.path:
            entries = []
            for media in traverse_obj(data, ('media_metadata', ...), expected_type=dict):
                if not media.get('id') or media.get('e') != 'RedditVideo':
                    continue
                formats = []
                if media.get('hlsUrl'):
                    formats.extend(self._extract_m3u8_formats(
                        unescapeHTML(media['hlsUrl']), video_id, 'mp4', m3u8_id='hls', fatal=False))
                if media.get('dashUrl'):
                    formats.extend(self._extract_mpd_formats(
                        unescapeHTML(media['dashUrl']), video_id, mpd_id='dash', fatal=False))
                if formats:
                    entries.append({
                        'id': media['id'],
                        'display_id': video_id,
                        'formats': formats,
                        **info,
                    })
            if entries:
                return self.playlist_result(entries, video_id, **info)
            self.raise_no_formats('No media found', expected=True, video_id=video_id)
            return {**info, 'id': video_id}

        # Check if media is hosted on reddit:
        reddit_video = traverse_obj(data, (
            (None, ('crosspost_parent_list', ...)), ('secure_media', 'media'), 'reddit_video'), get_all=False)
        if reddit_video:
            playlist_urls = [
                try_get(reddit_video, lambda x: unescapeHTML(x[y]))
                for y in ('dash_url', 'hls_url')
            ]

            # Update video_id
            display_id = video_id
            video_id = self._search_regex(
                r'https?://v\.redd\.it/(?P<id>[^/?#&]+)', reddit_video['fallback_url'],
                'video_id', default=display_id)

            dash_playlist_url = playlist_urls[0] or f'https://v.redd.it/{video_id}/DASHPlaylist.mpd'
            hls_playlist_url = playlist_urls[1] or f'https://v.redd.it/{video_id}/HLSPlaylist.m3u8'
            qs = traverse_obj(parse_qs(hls_playlist_url), {
                'f': ('f', 0, {lambda x: ','.join([x, 'subsAll']) if x else 'hd,subsAll'}),
            })
            hls_playlist_url = update_url_query(hls_playlist_url, qs)

            formats = [{
                'url': unescapeHTML(reddit_video['fallback_url']),
                'height': int_or_none(reddit_video.get('height')),
                'width': int_or_none(reddit_video.get('width')),
                'tbr': int_or_none(reddit_video.get('bitrate_kbps')),
                'acodec': 'none',
                'vcodec': 'h264',
                'ext': 'mp4',
                'format_id': 'fallback',
                'format_note': 'DASH video, mp4_dash',
            }]
            hls_fmts, subtitles = self._extract_m3u8_formats_and_subtitles(
                hls_playlist_url, display_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(hls_fmts)
            dash_fmts, dash_subs = self._extract_mpd_formats_and_subtitles(
                dash_playlist_url, display_id, mpd_id='dash', fatal=False)
            formats.extend(dash_fmts)
            self._merge_subtitles(dash_subs, target=subtitles)

            return {
                **info,
                'id': video_id,
                'display_id': display_id,
                'formats': formats,
                'subtitles': subtitles or self.extract_subtitles(video_id),
                'duration': int_or_none(reddit_video.get('duration')),
            }

        if parsed_url.netloc == 'v.redd.it':
            self.raise_no_formats('This video is processing', expected=True, video_id=video_id)
            return {
                **info,
                'id': parsed_url.path.split('/')[1],
                'display_id': video_id,
            }

        # Not hosted on reddit, must continue extraction
        return {
            **info,
            'display_id': video_id,
            '_type': 'url_transparent',
            'url': video_url,
        }