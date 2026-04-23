def _real_extract(self, url):
        username, story_id = self._match_valid_url(url).group('user', 'id')
        if username == 'highlights' and not story_id:  # story id is only mandatory for highlights
            raise ExtractorError('Input URL is missing a highlight ID', expected=True)
        display_id = story_id or username
        story_info = self._download_webpage(url, display_id)
        user_info = self._search_json(r'"user":', story_info, 'user info', display_id, fatal=False)
        if not user_info:
            self.raise_login_required('This content is unreachable')

        user_id = traverse_obj(user_info, 'pk', 'id', expected_type=str)
        if username == 'highlights':
            story_info_url = f'highlight:{story_id}'
        else:
            if not user_id:  # user id is only mandatory for non-highlights
                raise ExtractorError('Unable to extract user id')
            story_info_url = user_id

        videos = traverse_obj(self._download_json(
            f'{self._API_BASE_URL}/feed/reels_media/?reel_ids={story_info_url}',
            display_id, errnote=False, fatal=False, headers=self._api_headers), 'reels')
        if not videos:
            self.raise_login_required('You need to log in to access this content')
        user_info = traverse_obj(videos, (user_id, 'user', {dict})) or {}

        full_name = traverse_obj(videos, (f'highlight:{story_id}', 'user', 'full_name'), (user_id, 'user', 'full_name'))
        story_title = traverse_obj(videos, (f'highlight:{story_id}', 'title'))
        if not story_title:
            story_title = f'Story by {username}'

        highlights = traverse_obj(videos, (f'highlight:{story_id}', 'items'), (user_id, 'items'))
        info_data = []
        for highlight in highlights:
            highlight.setdefault('user', {}).update(user_info)
            highlight_data = self._extract_product(highlight)
            if highlight_data.get('formats'):
                info_data.append({
                    'uploader': full_name,
                    'uploader_id': user_id,
                    **filter_dict(highlight_data),
                })
        if username != 'highlights' and story_id and not self._yes_playlist(username, story_id):
            return traverse_obj(info_data, (lambda _, v: v['id'] == _pk_to_id(story_id), any))

        return self.playlist_result(info_data, playlist_id=story_id, playlist_title=story_title)