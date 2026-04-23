def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        chapter_id, lecture_id, course_id = mobj.group('chapter_id', 'lesson_id', 'course_id')
        item_id = course_id if course_id else '%s-%s' % (chapter_id, lecture_id)

        webpage = self._download_webpage(url, item_id)

        # course path
        if course_id:
            module = self._parse_json(
                self._search_regex(
                    r'window\.module\s*=\s*({.+?})\s*;', webpage, 'module'),
                item_id)
            entries = []
            chapter_number = None
            chapter = None
            chapter_id = None
            for item in module['items']:
                if not isinstance(item, dict):
                    continue

                def type_field(key):
                    return (try_get(item, lambda x: x['type'][key], compat_str) or '').lower()
                type_fields = (type_field('name'), type_field('slug'))
                # Move to next module section
                if 'section' in type_fields:
                    chapter = item.get('course_name')
                    chapter_id = item.get('course_module')
                    chapter_number = 1 if not chapter_number else chapter_number + 1
                    continue
                # Skip non-lessons
                if 'lesson' not in type_fields:
                    continue
                lesson_url = urljoin(url, item.get('url'))
                if not lesson_url:
                    continue
                title = item.get('title') or item.get('lesson_name')
                description = item.get('md_desc') or clean_html(item.get('description')) or clean_html(item.get('text'))
                entries.append({
                    '_type': 'url_transparent',
                    'url': lesson_url,
                    'ie_key': LinuxAcademyIE.ie_key(),
                    'title': title,
                    'description': description,
                    'timestamp': unified_timestamp(item.get('date')) or unified_timestamp(item.get('created_on')),
                    'duration': parse_duration(item.get('duration')),
                    'chapter': chapter,
                    'chapter_id': chapter_id,
                    'chapter_number': chapter_number,
                })
            return {
                '_type': 'playlist',
                'entries': entries,
                'id': course_id,
                'title': module.get('title'),
                'description': module.get('md_desc') or clean_html(module.get('desc')),
                'duration': parse_duration(module.get('duration')),
            }

        # single video path
        m3u8_url = self._parse_json(
            self._search_regex(
                r'player\.playlist\s*=\s*(\[.+?\])\s*;', webpage, 'playlist'),
            item_id)[0]['file']
        formats = self._extract_m3u8_formats(
            m3u8_url, item_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')
        self._sort_formats(formats)
        info = {
            'id': item_id,
            'formats': formats,
        }
        lesson = self._parse_json(
            self._search_regex(
                (r'window\.lesson\s*=\s*({.+?})\s*;',
                 r'player\.lesson\s*=\s*({.+?})\s*;'),
                webpage, 'lesson', default='{}'), item_id, fatal=False)
        if lesson:
            info.update({
                'title': lesson.get('lesson_name'),
                'description': lesson.get('md_desc') or clean_html(lesson.get('desc')),
                'timestamp': unified_timestamp(lesson.get('date')) or unified_timestamp(lesson.get('created_on')),
                'duration': parse_duration(lesson.get('duration')),
            })
        if not info.get('title'):
            info['title'] = self._search_regex(
                (r'>Lecture\s*:\s*(?P<value>[^<]+)',
                 r'lessonName\s*=\s*(["\'])(?P<value>(?:(?!\1).)+)\1'), webpage,
                'title', group='value')
        return info