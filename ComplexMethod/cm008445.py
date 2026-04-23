def _real_extract(self, url):
        video_id = self._match_id(url)
        if urllib.parse.urlparse(url).netloc in ['www.ntr.nl', 'ntr.nl']:
            player = self._download_json(
                f'https://www.ntr.nl/ajax/player/embed/{video_id}', video_id,
                'Downloading player JSON', query={
                    'parameters[elementId]': f'npo{random.randint(0, 999)}',
                    'parameters[sterReferralUrl]': url,
                    'parameters[autoplay]': 0,
                })
        else:
            self._request_webpage(
                'https://www.npostart.nl/api/token', video_id,
                'Downloading token', headers={
                    'Referer': url,
                    'X-Requested-With': 'XMLHttpRequest',
                })
            player = self._download_json(
                f'https://www.npostart.nl/player/{video_id}', video_id,
                'Downloading player JSON', data=urlencode_postdata({
                    'autoplay': 0,
                    'share': 1,
                    'pageUrl': url,
                    'hasAdConsent': 0,
                }), headers={
                    'x-xsrf-token': try_call(lambda: urllib.parse.unquote(
                        self._get_cookies('https://www.npostart.nl')['XSRF-TOKEN'].value)),
                })

        player_token = player['token']

        drm = False
        format_urls = set()
        formats = []
        for profile in ('hls', 'dash-widevine', 'dash-playready', 'smooth'):
            streams = self._download_json(
                f'https://start-player.npo.nl/video/{video_id}/streams',
                video_id, f'Downloading {profile} profile JSON', fatal=False,
                query={
                    'profile': profile,
                    'quality': 'npoplus',
                    'tokenId': player_token,
                    'streamType': 'broadcast',
                }, data=b'')  # endpoint requires POST
            if not streams:
                continue
            stream = streams.get('stream')
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('src'))
            if not stream_url or stream_url in format_urls:
                continue
            format_urls.add(stream_url)
            if stream.get('protection') is not None or stream.get('keySystemOptions') is not None:
                drm = True
                continue
            stream_type = stream.get('type')
            stream_ext = determine_ext(stream_url)
            if stream_type == 'application/dash+xml' or stream_ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    stream_url, video_id, mpd_id='dash', fatal=False))
            elif stream_type == 'application/vnd.apple.mpegurl' or stream_ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
            elif re.search(r'\.isml?/Manifest', stream_url):
                formats.extend(self._extract_ism_formats(
                    stream_url, video_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'url': stream_url,
                })

        if not formats:
            if not self.get_param('allow_unplayable_formats') and drm:
                self.report_drm(video_id)

        info = {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }

        embed_url = url_or_none(player.get('embedUrl'))
        if embed_url:
            webpage = self._download_webpage(
                embed_url, video_id, 'Downloading embed page', fatal=False)
            if webpage:
                video = self._parse_json(
                    self._search_regex(
                        r'\bvideo\s*=\s*({.+?})\s*;', webpage, 'video',
                        default='{}'), video_id)
                if video:
                    title = video.get('episodeTitle')
                    subtitles = {}
                    subtitles_list = video.get('subtitles')
                    if isinstance(subtitles_list, list):
                        for cc in subtitles_list:
                            cc_url = url_or_none(cc.get('src'))
                            if not cc_url:
                                continue
                            lang = str_or_none(cc.get('language')) or 'nl'
                            subtitles.setdefault(lang, []).append({
                                'url': cc_url,
                            })
                    return merge_dicts({
                        'title': title,
                        'description': video.get('description'),
                        'thumbnail': url_or_none(
                            video.get('still_image_url') or video.get('orig_image_url')),
                        'duration': int_or_none(video.get('duration')),
                        'timestamp': unified_timestamp(video.get('broadcastDate')),
                        'creator': video.get('channel'),
                        'series': video.get('title'),
                        'episode': title,
                        'episode_number': int_or_none(video.get('episodeNumber')),
                        'subtitles': subtitles,
                    }, info)

        return info