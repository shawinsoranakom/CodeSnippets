def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        url, course_id = mobj.group('url', 'id')

        course = self._download_json(
            self._STATIC_PRODUCTS_BASE + f'{course_id}/toc', course_id)
        metadata = self._download_json(
            self._STATIC_PRODUCTS_BASE + f'{course_id}/summary',
            course_id, fatal=False) or {}

        entries = []
        for chapter_num, chapter in enumerate(course['chapters'], 1):
            chapter_id = str_or_none(chapter.get('id'))
            sections = chapter.get('sections')
            if not chapter_id or not isinstance(sections, list):
                continue
            chapter_info = {
                'chapter': chapter.get('title'),
                'chapter_number': chapter_num,
                'chapter_id': chapter_id,
            }
            for section in sections:
                section_id = str_or_none(section.get('id'))
                if not section_id or section.get('contentType') != 'video':
                    continue
                entry = {
                    '_type': 'url_transparent',
                    'url': '/'.join([url, chapter_id, section_id]),
                    'title': strip_or_none(section.get('title')),
                    'description': clean_html(section.get('summary')),
                    'thumbnail': metadata.get('coverImage'),
                    'timestamp': unified_timestamp(metadata.get('publicationDate')),
                    'ie_key': PacktPubIE.ie_key(),
                }
                entry.update(chapter_info)
                entries.append(entry)

        return self.playlist_result(
            entries, course_id, metadata.get('title'),
            clean_html(metadata.get('about')))