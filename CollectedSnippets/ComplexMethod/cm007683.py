def _extract_lesson(chapters, lesson_id, lesson):
        title = lesson.get('title') or lesson_id
        display_id = lesson.get('slug')
        description = lesson.get('description')
        thumbnail = lesson.get('thumbnail')

        chapter_number = None
        index = lesson.get('index')
        element_index = lesson.get('elementIndex')
        if (isinstance(index, int) and isinstance(element_index, int)
                and index < element_index):
            chapter_number = element_index - index
        chapter = (chapters[chapter_number - 1]
                   if chapter_number - 1 < len(chapters) else None)

        duration = None
        timestamp = lesson.get('timestamp')
        if isinstance(timestamp, compat_str):
            mobj = re.search(
                r'(?P<start>\d{1,2}:\d{1,2}:\d{1,2})\s*-(?P<end>\s*\d{1,2}:\d{1,2}:\d{1,2})',
                timestamp)
            if mobj:
                duration = parse_duration(mobj.group('end')) - parse_duration(
                    mobj.group('start'))

        return {
            '_type': 'url_transparent',
            'url': 'frontendmasters:%s' % lesson_id,
            'ie_key': FrontendMastersIE.ie_key(),
            'id': lesson_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'chapter': chapter,
            'chapter_number': chapter_number,
        }