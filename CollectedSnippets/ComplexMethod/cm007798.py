def _real_extract(self, url):
        course_path = self._match_id(url)

        webpage = self._download_webpage(url, course_path)

        course_id, title = self._extract_course_info(webpage, course_path)

        self._enroll_course(url, webpage, course_id)

        response = self._download_json(
            'https://www.udemy.com/api-2.0/courses/%s/cached-subscriber-curriculum-items' % course_id,
            course_id, 'Downloading course curriculum', query={
                'fields[chapter]': 'title,object_index',
                'fields[lecture]': 'title,asset',
                'page_size': '1000',
            })

        entries = []
        chapter, chapter_number = [None] * 2
        for entry in response['results']:
            clazz = entry.get('_class')
            if clazz == 'lecture':
                asset = entry.get('asset')
                if isinstance(asset, dict):
                    asset_type = asset.get('asset_type') or asset.get('assetType')
                    if asset_type != 'Video':
                        continue
                lecture_id = entry.get('id')
                if lecture_id:
                    entry = {
                        '_type': 'url_transparent',
                        'url': 'https://www.udemy.com/%s/learn/v4/t/lecture/%s' % (course_path, entry['id']),
                        'title': entry.get('title'),
                        'ie_key': UdemyIE.ie_key(),
                    }
                    if chapter_number:
                        entry['chapter_number'] = chapter_number
                    if chapter:
                        entry['chapter'] = chapter
                    entries.append(entry)
            elif clazz == 'chapter':
                chapter_number = entry.get('object_index')
                chapter = entry.get('title')

        return self.playlist_result(entries, course_id, title)