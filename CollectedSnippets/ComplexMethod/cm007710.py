def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = re.match(self._VALID_URL, url)
        course_id = mobj.group('course_id')
        video_id = mobj.group('id')

        base_url = smuggled_data.get('base_url') or self._extract_base_url(course_id, video_id)

        settings = self._download_xml(
            '%s/content/content_%s/videosettings.xml?v=1' % (base_url, video_id),
            video_id, 'Downloading video settings XML')

        _, title = self._extract_chapter_and_title(xpath_text(
            settings, './/Title', 'title', fatal=True))

        formats = []

        for sources in settings.findall(compat_xpath('.//MediaSources')):
            sources_type = sources.get('videoType')
            for source in sources.findall(compat_xpath('./MediaSource')):
                video_url = source.text
                if not video_url or not video_url.startswith('http'):
                    continue
                if sources_type == 'smoothstreaming':
                    formats.extend(self._extract_ism_formats(
                        video_url, video_id, 'mss', fatal=False))
                    continue
                video_mode = source.get('videoMode')
                height = int_or_none(self._search_regex(
                    r'^(\d+)[pP]$', video_mode or '', 'height', default=None))
                codec = source.get('codec')
                acodec, vcodec = [None] * 2
                if codec:
                    codecs = codec.split(',')
                    if len(codecs) == 2:
                        acodec, vcodec = codecs
                    elif len(codecs) == 1:
                        vcodec = codecs[0]
                formats.append({
                    'url': video_url,
                    'format_id': video_mode,
                    'height': height,
                    'acodec': acodec,
                    'vcodec': vcodec,
                })
        self._sort_formats(formats)

        subtitles = {}
        for source in settings.findall(compat_xpath('.//MarkerResourceSource')):
            subtitle_url = source.text
            if not subtitle_url:
                continue
            subtitles.setdefault('en', []).append({
                'url': '%s/%s' % (base_url, subtitle_url),
                'ext': source.get('type'),
            })

        return {
            'id': video_id,
            'title': title,
            'subtitles': subtitles,
            'formats': formats
        }