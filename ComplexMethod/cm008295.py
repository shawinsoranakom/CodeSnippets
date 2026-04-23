def _entries(self, user_id, is_user):
        prefix, suffix = ('users', 'videos') if is_user else ('creators', 'exclusive')
        next_page_url = f'https://xhamster.com/{prefix}/{user_id}/{suffix}/1'
        for pagenum in itertools.count(1):
            page = self._download_webpage(
                next_page_url, user_id, f'Downloading page {pagenum}')
            for video_tag in re.findall(
                    r'(<a[^>]+class=["\'].*?\bvideo-thumb__image-container[^>]+>)',
                    page):
                video = extract_attributes(video_tag)
                video_url = url_or_none(video.get('href'))
                if not video_url or not XHamsterIE.suitable(video_url):
                    continue
                video_id = XHamsterIE._match_id(video_url)
                yield self.url_result(
                    video_url, ie=XHamsterIE.ie_key(), video_id=video_id)
            mobj = re.search(r'<a[^>]+data-page=["\']next[^>]+>', page)
            if not mobj:
                break
            next_page = extract_attributes(mobj.group(0))
            next_page_url = url_or_none(next_page.get('href'))
            if not next_page_url:
                break