def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        course_path = mobj.group('coursepath')
        course_id = mobj.group('courseid')

        item_template = 'https://www.lynda.com/%s/%%s-4.html' % course_path

        course = self._download_json(
            'https://www.lynda.com/ajax/player?courseId=%s&type=course' % course_id,
            course_id, 'Downloading course JSON', fatal=False)

        if not course:
            webpage = self._download_webpage(url, course_id)
            entries = [
                self.url_result(
                    item_template % video_id, ie=LyndaIE.ie_key(),
                    video_id=video_id)
                for video_id in re.findall(
                    r'data-video-id=["\'](\d+)', webpage)]
            return self.playlist_result(
                entries, course_id,
                self._og_search_title(webpage, fatal=False),
                self._og_search_description(webpage))

        if course.get('Status') == 'NotFound':
            raise ExtractorError(
                'Course %s does not exist' % course_id, expected=True)

        unaccessible_videos = 0
        entries = []

        # Might want to extract videos right here from video['Formats'] as it seems 'Formats' is not provided
        # by single video API anymore

        for chapter in course['Chapters']:
            for video in chapter.get('Videos', []):
                if video.get('HasAccess') is False:
                    unaccessible_videos += 1
                    continue
                video_id = video.get('ID')
                if video_id:
                    entries.append({
                        '_type': 'url_transparent',
                        'url': item_template % video_id,
                        'ie_key': LyndaIE.ie_key(),
                        'chapter': chapter.get('Title'),
                        'chapter_number': int_or_none(chapter.get('ChapterIndex')),
                        'chapter_id': compat_str(chapter.get('ID')),
                    })

        if unaccessible_videos > 0:
            self._downloader.report_warning(
                '%s videos are only available for members (or paid members) and will not be downloaded. '
                % unaccessible_videos + self._ACCOUNT_CREDENTIALS_HINT)

        course_title = course.get('Title')
        course_description = course.get('Description')

        return self.playlist_result(entries, course_id, course_title, course_description)