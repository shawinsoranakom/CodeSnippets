def _extract_desktop(self, url):
        start_time = int_or_none(urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query).get('fromTime', [None])[0])

        url, smuggled = unsmuggle_url(url, {})
        video_id, is_embed = self._match_valid_url(url).group('id', 'embed')
        mode = 'videoembed' if is_embed else 'video'

        webpage = self._download_webpage(
            f'https://ok.ru/{mode}/{video_id}', video_id,
            note='Downloading desktop webpage',
            headers={'Referer': smuggled['referrer']} if smuggled.get('referrer') else {})

        error = traverse_obj(webpage, {find_element(cls='vp_video_stub_txt')})
        # Direct link from boosty
        if (error == 'The author of this video has not been found or is blocked'
                and not smuggled.get('referrer') and mode == 'videoembed'):
            return self._extract_desktop(smuggle_url(url, {'referrer': 'https://boosty.to'}))
        elif error:
            raise ExtractorError(error, expected=True)
        elif '>Access to this video is restricted</div>' in webpage:
            self.raise_login_required()

        player = self._parse_json(
            unescapeHTML(self._search_regex(
                rf'data-options=(?P<quote>["\'])(?P<player>{{.+?{video_id}.+?}})(?P=quote)',
                webpage, 'player', group='player')),
            video_id)

        # embedded external player
        if player.get('isExternalPlayer') and player.get('url'):
            return self.url_result(player['url'])

        flashvars = player['flashvars']

        metadata = flashvars.get('metadata')
        if metadata:
            metadata = self._parse_json(metadata, video_id)
        else:
            data = {}
            st_location = flashvars.get('location')
            if st_location:
                data['st.location'] = st_location
            metadata = self._download_json(
                urllib.parse.unquote(flashvars['metadataUrl']),
                video_id, 'Downloading metadata JSON',
                data=urlencode_postdata(data))

        movie = metadata['movie']

        # Some embedded videos may not contain title in movie dict (e.g.
        # http://ok.ru/video/62036049272859-0) thus we allow missing title
        # here and it's going to be extracted later by an extractor that
        # will process the actual embed.
        provider = metadata.get('provider')
        title = movie['title'] if provider == 'UPLOADED_ODKL' else movie.get('title')

        thumbnail = movie.get('poster')
        duration = int_or_none(movie.get('duration'))

        author = metadata.get('author', {})
        uploader_id = author.get('id')
        uploader = author.get('name')

        upload_date = unified_strdate(self._html_search_meta(
            'ya:ovs:upload_date', webpage, 'upload date', default=None))

        age_limit = None
        adult = self._html_search_meta(
            'ya:ovs:adult', webpage, 'age limit', default=None)
        if adult:
            age_limit = 18 if adult == 'true' else 0

        like_count = int_or_none(metadata.get('likeCount'))

        subtitles = {}
        for sub in traverse_obj(metadata, ('movie', 'subtitleTracks', ...), expected_type=dict):
            sub_url = sub.get('url')
            if not sub_url:
                continue
            subtitles.setdefault(sub.get('language') or 'en', []).append({
                'url': sub_url,
                'ext': 'vtt',
            })

        info = {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'upload_date': upload_date,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'like_count': like_count,
            'age_limit': age_limit,
            'start_time': start_time,
            'subtitles': subtitles,
        }

        if provider == 'USER_YOUTUBE':
            info.update({
                '_type': 'url_transparent',
                'url': movie['contentId'],
            })
            return info

        assert title
        if provider == 'LIVE_TV_APP':
            info['title'] = title

        quality = qualities(('4', '0', '1', '2', '3', '5', '6', '7'))

        formats = [{
            'url': f['url'],
            'ext': 'mp4',
            'format_id': f.get('name'),
        } for f in traverse_obj(metadata, ('videos', lambda _, v: url_or_none(v['url'])))]

        m3u8_url = traverse_obj(metadata, 'hlsManifestUrl', 'ondemandHls')
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))
            self._clear_cookies(m3u8_url)

        for mpd_id, mpd_key in [('dash', 'ondemandDash'), ('webm', 'metadataWebmUrl')]:
            mpd_url = metadata.get(mpd_key)
            if mpd_url:
                formats.extend(self._extract_mpd_formats(
                    mpd_url, video_id, mpd_id=mpd_id, fatal=False))
                self._clear_cookies(mpd_url)

        dash_manifest = metadata.get('metadataEmbedded')
        if dash_manifest:
            formats.extend(self._parse_mpd_formats(
                compat_etree_fromstring(dash_manifest), 'mpd'))

        for fmt in formats:
            fmt_type = self._search_regex(
                r'\btype[/=](\d)', fmt['url'],
                'format type', default=None)
            if fmt_type:
                fmt['quality'] = quality(fmt_type)

        # Live formats
        m3u8_url = metadata.get('hlsMasterPlaylistUrl')
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            self._clear_cookies(m3u8_url)
        rtmp_url = metadata.get('rtmpUrl')
        if rtmp_url:
            formats.append({
                'url': rtmp_url,
                'format_id': 'rtmp',
                'ext': 'flv',
            })

        if not formats:
            payment_info = metadata.get('paymentInfo')
            if payment_info:
                self.raise_no_formats('This video is paid, subscribe to download it', expected=True)

        info['formats'] = formats
        return info