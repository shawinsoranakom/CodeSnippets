def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        if re.search(r'alert\(["\']This video has been deleted', webpage):
            raise ExtractorError(
                'Video %s has been deleted' % video_id, expected=True)

        station_id = self._search_regex(
            r'nStationNo\s*=\s*(\d+)', webpage, 'station')
        bbs_id = self._search_regex(
            r'nBbsNo\s*=\s*(\d+)', webpage, 'bbs')
        video_id = self._search_regex(
            r'nTitleNo\s*=\s*(\d+)', webpage, 'title', default=video_id)

        partial_view = False
        for _ in range(2):
            query = {
                'nTitleNo': video_id,
                'nStationNo': station_id,
                'nBbsNo': bbs_id,
            }
            if partial_view:
                query['partialView'] = 'SKIP_ADULT'
            video_xml = self._download_xml(
                'http://afbbs.afreecatv.com:8080/api/video/get_video_info.php',
                video_id, 'Downloading video info XML%s'
                % (' (skipping adult)' if partial_view else ''),
                video_id, headers={
                    'Referer': url,
                }, query=query)

            flag = xpath_text(video_xml, './track/flag', 'flag', default=None)
            if flag and flag == 'SUCCEED':
                break
            if flag == 'PARTIAL_ADULT':
                self._downloader.report_warning(
                    'In accordance with local laws and regulations, underage users are restricted from watching adult content. '
                    'Only content suitable for all ages will be downloaded. '
                    'Provide account credentials if you wish to download restricted content.')
                partial_view = True
                continue
            elif flag == 'ADULT':
                error = 'Only users older than 19 are able to watch this video. Provide account credentials to download this content.'
            else:
                error = flag
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error), expected=True)
        else:
            raise ExtractorError('Unable to download video info')

        video_element = video_xml.findall(compat_xpath('./track/video'))[-1]
        if video_element is None or video_element.text is None:
            raise ExtractorError(
                'Video %s does not exist' % video_id, expected=True)

        video_url = video_element.text.strip()

        title = xpath_text(video_xml, './track/title', 'title', fatal=True)

        uploader = xpath_text(video_xml, './track/nickname', 'uploader')
        uploader_id = xpath_text(video_xml, './track/bj_id', 'uploader id')
        duration = int_or_none(xpath_text(
            video_xml, './track/duration', 'duration'))
        thumbnail = xpath_text(video_xml, './track/titleImage', 'thumbnail')

        common_entry = {
            'uploader': uploader,
            'uploader_id': uploader_id,
            'thumbnail': thumbnail,
        }

        info = common_entry.copy()
        info.update({
            'id': video_id,
            'title': title,
            'duration': duration,
        })

        if not video_url:
            entries = []
            file_elements = video_element.findall(compat_xpath('./file'))
            one = len(file_elements) == 1
            for file_num, file_element in enumerate(file_elements, start=1):
                file_url = url_or_none(file_element.text)
                if not file_url:
                    continue
                key = file_element.get('key', '')
                upload_date = self._search_regex(
                    r'^(\d{8})_', key, 'upload date', default=None)
                file_duration = int_or_none(file_element.get('duration'))
                format_id = key if key else '%s_%s' % (video_id, file_num)
                if determine_ext(file_url) == 'm3u8':
                    formats = self._extract_m3u8_formats(
                        file_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls',
                        note='Downloading part %d m3u8 information' % file_num)
                else:
                    formats = [{
                        'url': file_url,
                        'format_id': 'http',
                    }]
                if not formats:
                    continue
                self._sort_formats(formats)
                file_info = common_entry.copy()
                file_info.update({
                    'id': format_id,
                    'title': title if one else '%s (part %d)' % (title, file_num),
                    'upload_date': upload_date,
                    'duration': file_duration,
                    'formats': formats,
                })
                entries.append(file_info)
            entries_info = info.copy()
            entries_info.update({
                '_type': 'multi_video',
                'entries': entries,
            })
            return entries_info

        info = {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'duration': duration,
            'thumbnail': thumbnail,
        }

        if determine_ext(video_url) == 'm3u8':
            info['formats'] = self._extract_m3u8_formats(
                video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls')
        else:
            app, playpath = video_url.split('mp4:')
            info.update({
                'url': app,
                'ext': 'flv',
                'play_path': 'mp4:' + playpath,
                'rtmp_live': True,  # downloading won't end without this
            })

        return info