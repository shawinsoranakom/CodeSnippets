def _real_extract(self, url):
        username, slug = self._match_valid_url(url).groups()
        board = self._call_api(
            'Board', slug, {
                'slug': slug,
                'username': username,
            })['data']
        board_id = board['id']
        options = {
            'board_id': board_id,
            'page_size': 250,
        }
        bookmark = None
        entries = []
        while True:
            if bookmark:
                options['bookmarks'] = [bookmark]
            board_feed = self._call_api('BoardFeed', board_id, options)
            for item in (board_feed.get('data') or []):
                if not isinstance(item, dict) or item.get('type') != 'pin':
                    continue
                video_id = item.get('id')
                if video_id:
                    # Some pins may not be available anonymously via pin URL
                    # video = self._extract_video(item, extract_formats=False)
                    # video.update({
                    #     '_type': 'url_transparent',
                    #     'url': 'https://www.pinterest.com/pin/%s/' % video_id,
                    # })
                    # entries.append(video)
                    entries.append(self._extract_video(item))
            bookmark = board_feed.get('bookmark')
            if not bookmark:
                break
        return self.playlist_result(
            entries, playlist_id=board_id, playlist_title=board.get('name'))