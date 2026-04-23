def _get_old_info(self, video_id):
        metadata = self._download_json(
            'http://e.omroep.nl/metadata/%s' % video_id,
            video_id,
            # We have to remove the javascript callback
            transform_source=strip_jsonp,
        )

        error = metadata.get('error')
        if error:
            raise ExtractorError(error, expected=True)

        # For some videos actual video id (prid) is different (e.g. for
        # http://www.omroepwnl.nl/video/fragment/vandaag-de-dag-verkiezingen__POMS_WNL_853698
        # video id is POMS_WNL_853698 but prid is POW_00996502)
        video_id = metadata.get('prid') or video_id

        # titel is too generic in some cases so utilize aflevering_titel as well
        # when available (e.g. http://tegenlicht.vpro.nl/afleveringen/2014-2015/access-to-africa.html)
        title = metadata['titel']
        sub_title = metadata.get('aflevering_titel')
        if sub_title and sub_title != title:
            title += ': %s' % sub_title

        token = self._get_token(video_id)

        formats = []
        urls = set()

        def is_legal_url(format_url):
            return format_url and format_url not in urls and re.match(
                r'^(?:https?:)?//', format_url)

        QUALITY_LABELS = ('Laag', 'Normaal', 'Hoog')
        QUALITY_FORMATS = ('adaptive', 'wmv_sb', 'h264_sb', 'wmv_bb', 'h264_bb', 'wvc1_std', 'h264_std')

        quality_from_label = qualities(QUALITY_LABELS)
        quality_from_format_id = qualities(QUALITY_FORMATS)
        items = self._download_json(
            'http://ida.omroep.nl/app.php/%s' % video_id, video_id,
            'Downloading formats JSON', query={
                'adaptive': 'yes',
                'token': token,
            })['items'][0]
        for num, item in enumerate(items):
            item_url = item.get('url')
            if not is_legal_url(item_url):
                continue
            urls.add(item_url)
            format_id = self._search_regex(
                r'video/ida/([^/]+)', item_url, 'format id',
                default=None)

            item_label = item.get('label')

            def add_format_url(format_url):
                width = int_or_none(self._search_regex(
                    r'(\d+)[xX]\d+', format_url, 'width', default=None))
                height = int_or_none(self._search_regex(
                    r'\d+[xX](\d+)', format_url, 'height', default=None))
                if item_label in QUALITY_LABELS:
                    quality = quality_from_label(item_label)
                    f_id = item_label
                elif item_label in QUALITY_FORMATS:
                    quality = quality_from_format_id(format_id)
                    f_id = format_id
                else:
                    quality, f_id = [None] * 2
                formats.append({
                    'url': format_url,
                    'format_id': f_id,
                    'width': width,
                    'height': height,
                    'quality': quality,
                })

            # Example: http://www.npo.nl/de-nieuwe-mens-deel-1/21-07-2010/WO_VPRO_043706
            if item.get('contentType') in ('url', 'audio'):
                add_format_url(item_url)
                continue

            try:
                stream_info = self._download_json(
                    item_url + '&type=json', video_id,
                    'Downloading %s stream JSON'
                    % item_label or item.get('format') or format_id or num)
            except ExtractorError as ee:
                if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 404:
                    error = (self._parse_json(
                        ee.cause.read().decode(), video_id,
                        fatal=False) or {}).get('errorstring')
                    if error:
                        raise ExtractorError(error, expected=True)
                raise
            # Stream URL instead of JSON, example: npo:LI_NL1_4188102
            if isinstance(stream_info, compat_str):
                if not stream_info.startswith('http'):
                    continue
                video_url = stream_info
            # JSON
            else:
                video_url = stream_info.get('url')
            if not video_url or 'vodnotavailable.' in video_url or video_url in urls:
                continue
            urls.add(video_url)
            if determine_ext(video_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
            else:
                add_format_url(video_url)

        is_live = metadata.get('medium') == 'live'

        if not is_live:
            for num, stream in enumerate(metadata.get('streams', [])):
                stream_url = stream.get('url')
                if not is_legal_url(stream_url):
                    continue
                urls.add(stream_url)
                # smooth streaming is not supported
                stream_type = stream.get('type', '').lower()
                if stream_type in ['ss', 'ms']:
                    continue
                if stream_type == 'hds':
                    f4m_formats = self._extract_f4m_formats(
                        stream_url, video_id, fatal=False)
                    # f4m downloader downloads only piece of live stream
                    for f4m_format in f4m_formats:
                        f4m_format['preference'] = -1
                    formats.extend(f4m_formats)
                elif stream_type == 'hls':
                    formats.extend(self._extract_m3u8_formats(
                        stream_url, video_id, ext='mp4', fatal=False))
                # Example: http://www.npo.nl/de-nieuwe-mens-deel-1/21-07-2010/WO_VPRO_043706
                elif '.asf' in stream_url:
                    asx = self._download_xml(
                        stream_url, video_id,
                        'Downloading stream %d ASX playlist' % num,
                        transform_source=fix_xml_ampersands, fatal=False)
                    if not asx:
                        continue
                    ref = asx.find('./ENTRY/Ref')
                    if ref is None:
                        continue
                    video_url = ref.get('href')
                    if not video_url or video_url in urls:
                        continue
                    urls.add(video_url)
                    formats.append({
                        'url': video_url,
                        'ext': stream.get('formaat', 'asf'),
                        'quality': stream.get('kwaliteit'),
                        'preference': -10,
                    })
                else:
                    formats.append({
                        'url': stream_url,
                        'quality': stream.get('kwaliteit'),
                    })

        self._sort_formats(formats)

        subtitles = {}
        if metadata.get('tt888') == 'ja':
            subtitles['nl'] = [{
                'ext': 'vtt',
                'url': 'http://tt888.omroep.nl/tt888/%s' % video_id,
            }]

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'description': metadata.get('info'),
            'thumbnail': metadata.get('images', [{'url': None}])[-1]['url'],
            'upload_date': unified_strdate(metadata.get('gidsdatum')),
            'duration': parse_duration(metadata.get('tijdsduur')),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
        }