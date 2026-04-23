def _extract_webpage(self, url):
        mobj = re.match(self._VALID_URL, url)

        description = None

        presumptive_id = mobj.group('presumptive_id')
        display_id = presumptive_id
        if presumptive_id:
            webpage = self._download_webpage(url, display_id)

            description = strip_or_none(self._og_search_description(
                webpage, default=None) or self._html_search_meta(
                'description', webpage, default=None))
            upload_date = unified_strdate(self._search_regex(
                r'<input type="hidden" id="air_date_[0-9]+" value="([^"]+)"',
                webpage, 'upload date', default=None))

            # tabbed frontline videos
            MULTI_PART_REGEXES = (
                r'<div[^>]+class="videotab[^"]*"[^>]+vid="(\d+)"',
                r'<a[^>]+href=["\']#(?:video-|part)\d+["\'][^>]+data-cove[Ii]d=["\'](\d+)',
            )
            for p in MULTI_PART_REGEXES:
                tabbed_videos = orderedSet(re.findall(p, webpage))
                if tabbed_videos:
                    return tabbed_videos, presumptive_id, upload_date, description

            MEDIA_ID_REGEXES = [
                r"div\s*:\s*'videoembed'\s*,\s*mediaid\s*:\s*'(\d+)'",  # frontline video embed
                r'class="coveplayerid">([^<]+)<',                       # coveplayer
                r'<section[^>]+data-coveid="(\d+)"',                    # coveplayer from http://www.pbs.org/wgbh/frontline/film/real-csi/
                r'<input type="hidden" id="pbs_video_id_[0-9]+" value="([0-9]+)"/>',  # jwplayer
                r"(?s)window\.PBS\.playerConfig\s*=\s*{.*?id\s*:\s*'([0-9]+)',",
                r'<div[^>]+\bdata-cove-id=["\'](\d+)"',  # http://www.pbs.org/wgbh/roadshow/watch/episode/2105-indianapolis-hour-2/
                r'<iframe[^>]+\bsrc=["\'](?:https?:)?//video\.pbs\.org/widget/partnerplayer/(\d+)',  # https://www.pbs.org/wgbh/masterpiece/episodes/victoria-s2-e1/
            ]

            media_id = self._search_regex(
                MEDIA_ID_REGEXES, webpage, 'media ID', fatal=False, default=None)
            if media_id:
                return media_id, presumptive_id, upload_date, description

            # Frontline video embedded via flp
            video_id = self._search_regex(
                r'videoid\s*:\s*"([\d+a-z]{7,})"', webpage, 'videoid', default=None)
            if video_id:
                # pkg_id calculation is reverse engineered from
                # http://www.pbs.org/wgbh/pages/frontline/js/flp2012.js
                prg_id = self._search_regex(
                    r'videoid\s*:\s*"([\d+a-z]{7,})"', webpage, 'videoid')[7:]
                if 'q' in prg_id:
                    prg_id = prg_id.split('q')[1]
                prg_id = int(prg_id, 16)
                getdir = self._download_json(
                    'http://www.pbs.org/wgbh/pages/frontline/.json/getdir/getdir%d.json' % prg_id,
                    presumptive_id, 'Downloading getdir JSON',
                    transform_source=strip_jsonp)
                return getdir['mid'], presumptive_id, upload_date, description

            for iframe in re.findall(r'(?s)<iframe(.+?)></iframe>', webpage):
                url = self._search_regex(
                    r'src=(["\'])(?P<url>.+?partnerplayer.+?)\1', iframe,
                    'player URL', default=None, group='url')
                if url:
                    break

            if not url:
                url = self._og_search_url(webpage)

            mobj = re.match(
                self._VALID_URL, self._proto_relative_url(url.strip()))

        player_id = mobj.group('player_id')
        if not display_id:
            display_id = player_id
        if player_id:
            player_page = self._download_webpage(
                url, display_id, note='Downloading player page',
                errnote='Could not download player page')
            video_id = self._search_regex(
                r'<div\s+id=["\']video_(\d+)', player_page, 'video ID',
                default=None)
            if not video_id:
                video_info = self._extract_video_data(
                    player_page, 'video data', display_id)
                video_id = compat_str(
                    video_info.get('id') or video_info['contentID'])
        else:
            video_id = mobj.group('id')
            display_id = video_id

        return video_id, display_id, None, description