def _real_extract(self, url):
        video_id, url_date, url_date_2 = self._match_valid_url(url).group('id', 'date', 'date2')
        url_date = url_date or url_date_2

        video_info = self._download_json(
            'https://web.archive.org/__wb/videoinfo', video_id,
            query={'vtype': 'youtube', 'vid': video_id})

        if not traverse_obj(video_info, 'formats'):
            self.raise_no_formats(
                'The requested video is not archived or indexed', expected=True)

        capture_dates = self._get_capture_dates(video_id, int_or_none(url_date))
        self.write_debug('Captures to try: ' + join_nonempty(*capture_dates, delim=', '))
        info = {'id': video_id}
        for capture in capture_dates:
            webpage = self._download_webpage(
                (self._WAYBACK_BASE_URL + 'http://www.youtube.com/watch?v=%s') % (capture, video_id),
                video_id=video_id, fatal=False, errnote='unable to download capture webpage (it may not be archived)',
                note='Downloading capture webpage')
            current_info = self._extract_metadata(video_id, webpage or '')
            # Try avoid getting deleted video metadata
            if current_info.get('title'):
                info = merge_dicts(info, current_info)
                if 'captures' not in self._configuration_arg('check_all'):
                    break

        info['thumbnails'] = self._extract_thumbnails(video_id)

        formats = []
        if video_info.get('dmux'):
            for vf in traverse_obj(video_info, ('formats', 'video', lambda _, v: url_or_none(v['url']))):
                formats.append(self._parse_fmt(vf, {'acodec': 'none'}))
            for af in traverse_obj(video_info, ('formats', 'audio', lambda _, v: url_or_none(v['url']))):
                formats.append(self._parse_fmt(af, {'vcodec': 'none'}))
        else:
            for fmt in traverse_obj(video_info, ('formats', lambda _, v: url_or_none(v['url']))):
                formats.append(self._parse_fmt(fmt))
        info['formats'] = formats

        return info