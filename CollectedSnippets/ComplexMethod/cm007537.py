def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('video_id')
        if not video_id:
            if mobj.group('token') is not None:
                # The video id is in the redirected url
                self.to_screen('Getting video id')
                request = HEADRequest(url)
                _, urlh = self._download_webpage_handle(request, 'NA', False)
                return self._real_extract(urlh.geturl())
            else:
                pseudo_id = mobj.group('pseudo_id')
                webpage = self._download_webpage(url, pseudo_id)
                error = get_element_by_attribute('class', 'errtitle', webpage)
                if error:
                    raise ExtractorError('%s said: %s' % (
                        self.IE_NAME, clean_html(error)), expected=True)
                video_id = self._search_regex(
                    r"video_id\s*:\s*'(\d+)'", webpage, 'video id')

        video_data = self._download_json(
            'http://s.video.sina.com.cn/video/h5play',
            video_id, query={'video_id': video_id})
        if video_data['code'] != 1:
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, video_data['message']), expected=True)
        else:
            video_data = video_data['data']
            title = video_data['title']
            description = video_data.get('description')
            if description:
                description = description.strip()

            preference = qualities(['cif', 'sd', 'hd', 'fhd', 'ffd'])
            formats = []
            for quality_id, quality in video_data.get('videos', {}).get('mp4', {}).items():
                file_api = quality.get('file_api')
                file_id = quality.get('file_id')
                if not file_api or not file_id:
                    continue
                formats.append({
                    'format_id': quality_id,
                    'url': update_url_query(file_api, {'vid': file_id}),
                    'preference': preference(quality_id),
                    'ext': 'mp4',
                })
            self._sort_formats(formats)

            return {
                'id': video_id,
                'title': title,
                'description': description,
                'thumbnail': video_data.get('image'),
                'duration': int_or_none(video_data.get('length')),
                'timestamp': int_or_none(video_data.get('create_time')),
                'formats': formats,
            }