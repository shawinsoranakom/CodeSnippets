def _real_extract(self, url):
        video_id, display_id, upload_date, description = self._extract_webpage(url)

        if isinstance(video_id, list):
            entries = [self.url_result(
                'http://video.pbs.org/video/%s' % vid_id, 'PBS', vid_id)
                for vid_id in video_id]
            return self.playlist_result(entries, display_id)

        info = None
        redirects = []
        redirect_urls = set()

        def extract_redirect_urls(info):
            for encoding_name in ('recommended_encoding', 'alternate_encoding'):
                redirect = info.get(encoding_name)
                if not redirect:
                    continue
                redirect_url = redirect.get('url')
                if redirect_url and redirect_url not in redirect_urls:
                    redirects.append(redirect)
                    redirect_urls.add(redirect_url)
            encodings = info.get('encodings')
            if isinstance(encodings, list):
                for encoding in encodings:
                    encoding_url = url_or_none(encoding)
                    if encoding_url and encoding_url not in redirect_urls:
                        redirects.append({'url': encoding_url})
                        redirect_urls.add(encoding_url)

        chapters = []
        # Player pages may also serve different qualities
        for page in ('widget/partnerplayer', 'portalplayer'):
            player = self._download_webpage(
                'http://player.pbs.org/%s/%s' % (page, video_id),
                display_id, 'Downloading %s page' % page, fatal=False)
            if player:
                video_info = self._extract_video_data(
                    player, '%s video data' % page, display_id, fatal=False)
                if video_info:
                    extract_redirect_urls(video_info)
                    if not info:
                        info = video_info
                if not chapters:
                    raw_chapters = video_info.get('chapters') or []
                    if not raw_chapters:
                        for chapter_data in re.findall(r'(?s)chapters\.push\(({.*?})\)', player):
                            chapter = self._parse_json(chapter_data, video_id, js_to_json, fatal=False)
                            if not chapter:
                                continue
                            raw_chapters.append(chapter)
                    for chapter in raw_chapters:
                        start_time = float_or_none(chapter.get('start_time'), 1000)
                        duration = float_or_none(chapter.get('duration'), 1000)
                        if start_time is None or duration is None:
                            continue
                        chapters.append({
                            'start_time': start_time,
                            'end_time': start_time + duration,
                            'title': chapter.get('title'),
                        })

        formats = []
        http_url = None
        for num, redirect in enumerate(redirects):
            redirect_id = redirect.get('eeid')

            redirect_info = self._download_json(
                '%s?format=json' % redirect['url'], display_id,
                'Downloading %s video url info' % (redirect_id or num),
                headers=self.geo_verification_headers())

            if redirect_info['status'] == 'error':
                message = self._ERRORS.get(
                    redirect_info['http_code'], redirect_info['message'])
                if redirect_info['http_code'] == 403:
                    self.raise_geo_restricted(
                        msg=message, countries=self._GEO_COUNTRIES)
                raise ExtractorError(
                    '%s said: %s' % (self.IE_NAME, message), expected=True)

            format_url = redirect_info.get('url')
            if not format_url:
                continue

            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, display_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': redirect_id,
                })
                if re.search(r'^https?://.*(?:\d+k|baseline)', format_url):
                    http_url = format_url
        self._remove_duplicate_formats(formats)
        m3u8_formats = list(filter(
            lambda f: f.get('protocol') == 'm3u8' and f.get('vcodec') != 'none',
            formats))
        if http_url:
            for m3u8_format in m3u8_formats:
                bitrate = self._search_regex(r'(\d+)k', m3u8_format['url'], 'bitrate', default=None)
                # Lower qualities (150k and 192k) are not available as HTTP formats (see [1]),
                # we won't try extracting them.
                # Since summer 2016 higher quality formats (4500k and 6500k) are also available
                # albeit they are not documented in [2].
                # 1. https://github.com/ytdl-org/youtube-dl/commit/cbc032c8b70a038a69259378c92b4ba97b42d491#commitcomment-17313656
                # 2. https://projects.pbs.org/confluence/display/coveapi/COVE+Video+Specifications
                if not bitrate or int(bitrate) < 400:
                    continue
                f_url = re.sub(r'\d+k|baseline', bitrate + 'k', http_url)
                # This may produce invalid links sometimes (e.g.
                # http://www.pbs.org/wgbh/frontline/film/suicide-plan)
                if not self._is_valid_url(f_url, display_id, 'http-%sk video' % bitrate):
                    continue
                f = m3u8_format.copy()
                f.update({
                    'url': f_url,
                    'format_id': m3u8_format['format_id'].replace('hls', 'http'),
                    'protocol': 'http',
                })
                formats.append(f)
        self._sort_formats(formats)

        rating_str = info.get('rating')
        if rating_str is not None:
            rating_str = rating_str.rpartition('-')[2]
        age_limit = US_RATINGS.get(rating_str)

        subtitles = {}
        closed_captions_url = info.get('closed_captions_url')
        if closed_captions_url:
            subtitles['en'] = [{
                'ext': 'ttml',
                'url': closed_captions_url,
            }]
            mobj = re.search(r'/(\d+)_Encoded\.dfxp', closed_captions_url)
            if mobj:
                ttml_caption_suffix, ttml_caption_id = mobj.group(0, 1)
                ttml_caption_id = int(ttml_caption_id)
                subtitles['en'].extend([{
                    'url': closed_captions_url.replace(
                        ttml_caption_suffix, '/%d_Encoded.srt' % (ttml_caption_id + 1)),
                    'ext': 'srt',
                }, {
                    'url': closed_captions_url.replace(
                        ttml_caption_suffix, '/%d_Encoded.vtt' % (ttml_caption_id + 2)),
                    'ext': 'vtt',
                }])

        # info['title'] is often incomplete (e.g. 'Full Episode', 'Episode 5', etc)
        # Try turning it to 'program - title' naming scheme if possible
        alt_title = info.get('program', {}).get('title')
        if alt_title:
            info['title'] = alt_title + ' - ' + re.sub(r'^' + alt_title + r'[\s\-:]+', '', info['title'])

        description = info.get('description') or info.get(
            'program', {}).get('description') or description

        return {
            'id': video_id,
            'display_id': display_id,
            'title': info['title'],
            'description': description,
            'thumbnail': info.get('image_url'),
            'duration': int_or_none(info.get('duration')),
            'age_limit': age_limit,
            'upload_date': upload_date,
            'formats': formats,
            'subtitles': subtitles,
            'chapters': chapters,
        }