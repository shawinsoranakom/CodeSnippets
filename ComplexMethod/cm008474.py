def _real_extract(self, url):
        course_name = self._match_id(url)

        webpage = self._download_webpage(url, course_name)

        props = self._parse_json(
            self._search_regex(r'data\s*=\s*({.+?})\s*;', webpage, 'data'),
            course_name)['initialProps']

        entries = []
        for chapter_num, chapter in enumerate(props['concepts'], 1):
            if not isinstance(chapter, dict):
                continue
            materials = chapter.get('materials')
            if not materials or not isinstance(materials, list):
                continue
            chapter_title = chapter.get('title')
            chapter_id = str_or_none(chapter.get('id'))
            for material in materials:
                if not isinstance(material, dict):
                    continue
                if material.get('material_type') != 'video':
                    continue
                video_url = urljoin(url, material.get('url'))
                if not video_url:
                    continue
                entries.append({
                    '_type': 'url_transparent',
                    'url': video_url,
                    'title': str_or_none(material.get('name')),
                    'id': str_or_none(material.get('id')),
                    'ie_key': PlatziIE.ie_key(),
                    'chapter': chapter_title,
                    'chapter_number': chapter_num,
                    'chapter_id': chapter_id,
                })

        course_id = str(try_get(props, lambda x: x['course']['id']))
        course_title = try_get(props, lambda x: x['course']['name'], str)

        return self.playlist_result(entries, course_id, course_title)