def _real_extract(self, url):
        locale, video_id = re.match(self._VALID_URL, url).groups()
        countries = [locale.split('-')[1].upper()]
        self._initialize_geo_bypass({
            'countries': countries,
        })

        try:
            item = self._download_json(
                # https://contentfeed.services.lego.com/api/v2/item/[VIDEO_ID]?culture=[LOCALE]&contentType=Video
                'https://services.slingshot.lego.com/mediaplayer/v2',
                video_id, query={
                    'videoId': '%s_%s' % (uuid.UUID(video_id), locale),
                }, headers=self.geo_verification_headers())
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 451:
                self.raise_geo_restricted(countries=countries)
            raise

        video = item['Video']
        video_id = video['Id']
        title = video['Title']

        q = qualities(['Lowest', 'Low', 'Medium', 'High', 'Highest'])
        formats = []
        for video_source in item.get('VideoFormats', []):
            video_source_url = video_source.get('Url')
            if not video_source_url:
                continue
            video_source_format = video_source.get('Format')
            if video_source_format == 'F4M':
                formats.extend(self._extract_f4m_formats(
                    video_source_url, video_id,
                    f4m_id=video_source_format, fatal=False))
            elif video_source_format == 'M3U8':
                formats.extend(self._extract_m3u8_formats(
                    video_source_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=video_source_format, fatal=False))
            else:
                video_source_quality = video_source.get('Quality')
                format_id = []
                for v in (video_source_format, video_source_quality):
                    if v:
                        format_id.append(v)
                f = {
                    'format_id': '-'.join(format_id),
                    'quality': q(video_source_quality),
                    'url': video_source_url,
                }
                quality = self._QUALITIES.get(video_source_quality)
                if quality:
                    f.update({
                        'abr': quality[0],
                        'height': quality[1],
                        'width': quality[2],
                    }),
                formats.append(f)
        self._sort_formats(formats)

        subtitles = {}
        sub_file_id = video.get('SubFileId')
        if sub_file_id and sub_file_id != '00000000-0000-0000-0000-000000000000':
            net_storage_path = video.get('NetstoragePath')
            invariant_id = video.get('InvariantId')
            video_file_id = video.get('VideoFileId')
            video_version = video.get('VideoVersion')
            if net_storage_path and invariant_id and video_file_id and video_version:
                subtitles.setdefault(locale[:2], []).append({
                    'url': 'https://lc-mediaplayerns-live-s.legocdn.com/public/%s/%s_%s_%s_%s_sub.srt' % (net_storage_path, invariant_id, video_file_id, locale, video_version),
                })

        return {
            'id': video_id,
            'title': title,
            'description': video.get('Description'),
            'thumbnail': video.get('GeneratedCoverImage') or video.get('GeneratedThumbnail'),
            'duration': int_or_none(video.get('Length')),
            'formats': formats,
            'subtitles': subtitles,
            'age_limit': int_or_none(video.get('AgeFrom')),
            'season': video.get('SeasonTitle'),
            'season_number': int_or_none(video.get('Season')) or None,
            'episode_number': int_or_none(video.get('Episode')) or None,
        }