def _real_extract(self, url):
        story_id = self._match_id(url)
        webpage = self._download_webpage(url, story_id)

        entries = []
        seen_ids = set()
        for idx, video_id in enumerate(re.findall(r'data-video(?:id)?="(\d+)"', webpage)):
            if video_id in seen_ids:
                continue
            seen_ids.add(video_id)
            entry = self._extract_video(video_id, webpage, fatal=False)
            if not entry:
                continue

            if idx >= 1:
                # Titles are duplicates, make them unique
                entry['title'] = '%s (%d)' % (entry['title'], idx)

            entries.append(entry)

        seen_ids = set()
        for yt_id in re.findall(
                r'data-id\s*=\s*["\']([\w-]+)[^>]+\bclass\s*=\s*["\']youtube\b',
                webpage):
            if yt_id in seen_ids:
                continue
            seen_ids.add(yt_id)
            if YoutubeIE.suitable(yt_id):
                entries.append(self.url_result(yt_id, ie='Youtube', video_id=yt_id))

        return self.playlist_result(
            entries, story_id,
            re.sub(self._TITLE_STRIP_RE, '', self._og_search_title(webpage, default='') or None))