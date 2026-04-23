def _real_extract(self, url):
        # starting download using infojson from this extractor is undefined behavior,
        # and never be fixed in the future; you must trigger downloads by directly specifying URL.
        # (unless there's a way to hook before downloading by extractor)
        video_id, video_type = self._match_valid_url(url).group('id', 'type')
        headers = {
            'Authorization': 'Bearer ' + self._get_device_token(),
        }
        video_type = video_type.split('/')[-1]

        webpage = self._download_webpage(url, video_id)
        canonical_url = self._search_regex(
            r'<link\s+rel="canonical"\s*href="(.+?)"', webpage, 'canonical URL',
            default=url)
        info = self._search_json_ld(webpage, video_id, default={})

        title = self._search_regex(
            r'<span\s*class=".+?EpisodeTitleBlock__title">(.+?)</span>', webpage, 'title', default=None)
        if not title:
            jsonld = None
            for jld in re.finditer(
                    r'(?is)<span\s*class="com-m-Thumbnail__image">(?:</span>)?<script[^>]+type=(["\']?)application/ld\+json\1[^>]*>(?P<json_ld>.+?)</script>',
                    webpage):
                jsonld = self._parse_json(jld.group('json_ld'), video_id, fatal=False)
                if jsonld:
                    break
            if jsonld:
                title = jsonld.get('caption')
        if not title and video_type == 'now-on-air':
            if not self._TIMETABLE:
                # cache the timetable because it goes to 5MiB in size (!!)
                self._TIMETABLE = self._download_json(
                    'https://api.abema.io/v1/timetable/dataSet?debug=false', video_id,
                    headers=headers)
            now = time_seconds(hours=9)
            for slot in self._TIMETABLE.get('slots', []):
                if slot.get('channelId') != video_id:
                    continue
                if slot['startAt'] <= now and now < slot['endAt']:
                    title = slot['title']
                    break

        # read breadcrumb on top of page
        breadcrumb = self._extract_breadcrumb_list(webpage, video_id)
        if breadcrumb:
            # breadcrumb list translates to: (e.g. 1st test for this IE)
            # Home > Anime (genre) > Isekai Shokudo 2 (series name) > Episode 1 "Cheese cakes" "Morning again" (episode title)
            # hence this works
            info['series'] = breadcrumb[-2]
            info['episode'] = breadcrumb[-1]
            if not title:
                title = info['episode']

        description = self._html_search_regex(
            (r'<p\s+class="com-video-EpisodeDetailsBlock__content"><span\s+class=".+?">(.+?)</span></p><div',
             r'<span\s+class=".+?SlotSummary.+?">(.+?)</span></div><div'),
            webpage, 'description', default=None, group=1)
        if not description:
            og_desc = self._html_search_meta(
                ('description', 'og:description', 'twitter:description'), webpage)
            if og_desc:
                description = re.sub(r'''(?sx)
                    ^(.+?)(?:
                        アニメの動画を無料で見るならABEMA！| # anime
                        等、.+ # applies for most of categories
                    )?
                ''', r'\1', og_desc)

        # canonical URL may contain season and episode number
        mobj = re.search(r's(\d+)_p(\d+)$', canonical_url)
        if mobj:
            seri = int_or_none(mobj.group(1), default=float('inf'))
            epis = int_or_none(mobj.group(2), default=float('inf'))
            info['season_number'] = seri if seri < 100 else None
            # some anime like Detective Conan (though not available in AbemaTV)
            # has more than 1000 episodes (1026 as of 2021/11/15)
            info['episode_number'] = epis if epis < 2000 else None

        is_live, m3u8_url = False, None
        availability = 'public'
        if video_type == 'now-on-air':
            is_live = True
            channel_url = 'https://api.abema.io/v1/channels'
            if video_id == 'news-global':
                channel_url = update_url_query(channel_url, {'division': '1'})
            onair_channels = self._download_json(channel_url, video_id)
            for ch in onair_channels['channels']:
                if video_id == ch['id']:
                    m3u8_url = ch['playback']['hls']
                    break
            else:
                raise ExtractorError(f'Cannot find on-air {video_id} channel.', expected=True)
        elif video_type == 'episode':
            api_response = self._download_json(
                f'https://api.abema.io/v1/video/programs/{video_id}', video_id,
                note='Checking playability',
                headers=headers)
            if not traverse_obj(api_response, ('label', 'free', {bool})):
                # cannot acquire decryption key for these streams
                self.report_warning('This is a premium-only stream')
                availability = 'premium_only'
            info.update(traverse_obj(api_response, {
                'series': ('series', 'title'),
                'season': ('season', 'name'),
                'season_number': ('season', 'sequence'),
                'episode_number': ('episode', 'number'),
            }))
            if not title:
                title = traverse_obj(api_response, ('episode', 'title'))
            if not description:
                description = traverse_obj(api_response, ('episode', 'content'))

            m3u8_url = f'https://vod-abematv.akamaized.net/program/{video_id}/playlist.m3u8'
        elif video_type == 'slots':
            api_response = self._download_json(
                f'https://api.abema.io/v1/media/slots/{video_id}', video_id,
                note='Checking playability',
                headers=headers)
            if not traverse_obj(api_response, ('slot', 'flags', 'timeshiftFree'), default=False):
                self.report_warning('This is a premium-only stream')
                availability = 'premium_only'

            m3u8_url = f'https://vod-abematv.akamaized.net/slot/{video_id}/playlist.m3u8'
        else:
            raise ExtractorError('Unreachable')

        if is_live:
            self.report_warning("This is a livestream; yt-dlp doesn't support downloading natively, but FFmpeg cannot handle m3u8 manifests from AbemaTV")
            self.report_warning('Please consider using Streamlink to download these streams (https://github.com/streamlink/streamlink)')
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, ext='mp4', live=is_live)

        info.update({
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'is_live': is_live,
            'availability': availability,
        })

        if thumbnail := update_url(self._og_search_thumbnail(webpage, default=''), query=None):
            info['thumbnails'] = [{'url': thumbnail}]

        return info