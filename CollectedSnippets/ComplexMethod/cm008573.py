def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        user = mobj.group('user') or mobj.group('user_2')
        kind = mobj.group('kind') or mobj.group('kind_2')
        display_id = mobj.group('id') or user

        if mobj.group('kind_2') == 'videos':
            data = {'from_user': display_id, 'album': -1, 'limit': 18, 'offset': 0, 'order': 'new2old', 'type': 'video'}
        elif kind in ('music/albums', 'music'):
            data = {'user': user, 'public_only': True, 'individual_limit': {'singles': 1, 'albums': 1, 'playlists': 1}}
        else:
            data = {'url_slug': display_id, 'children': 10, 'order': 'old2new'}

        method = 'getMusicOverview' if kind in ('music/albums', 'music') else 'getElements'
        json_data = self._call_api(method, display_id, data=data)
        if kind in ('music/albums', 'music'):
            json_data = json_data['singles']['list']

        entites = []
        for media in json_data:
            url = media.get('external_media_url') or media.get('link')
            if url.startswith('https://www.youtube.com'):
                entites.append({
                    '_type': 'url',
                    'url': url,
                    'ie_key': 'Youtube',
                })
                continue
            is_audio = (media.get('type') or '').lower() == 'audio'
            entites.append({
                'url': url,
                'id': media['id'],
                'title': media['title'],
                'duration': int_or_none(media.get('duration')),
                'timestamp': int_or_none(media.get('timestamp')),
                'album': try_get(media, lambda x: x['album']['title']),
                'uploader': try_get(media, lambda x: x['creator']['display_name']),
                'uploader_id': try_get(media, lambda x: x['creator']['id']),
                'thumbnail': media.get('image_comment'),
                'like_count': int_or_none(media.get('likes')),
                'vcodec': 'none' if is_audio else None,
                'ext': 'mp3' if is_audio else None,
            })

        if len(entites) > 1:
            return self.playlist_result(entites, display_id)

        return entites[0]