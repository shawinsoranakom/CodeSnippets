def _extract_set(self, playlist, token=None):
        playlist_id = str(playlist['id'])
        tracks = playlist.get('tracks') or []
        if not all(t.get('permalink_url') for t in tracks) and token:
            tracks = self._call_api(
                self._API_V2_BASE + 'tracks', playlist_id,
                'Downloading tracks', query={
                    'ids': ','.join([str(t['id']) for t in tracks]),
                    'playlistId': playlist_id,
                    'playlistSecretToken': token,
                }, headers=self._HEADERS)
        album_info = traverse_obj(playlist, {
            'album': ('title', {str}),
            'album_artist': ('user', 'username', {str}),
            'album_type': ('set_type', {str}, {lambda x: x or 'playlist'}),
        })
        entries = []
        for track in tracks:
            track_id = str_or_none(track.get('id'))
            url = track.get('permalink_url')
            if not url:
                if not track_id:
                    continue
                url = self._API_V2_BASE + 'tracks/' + track_id
                if token:
                    url += '?secret_token=' + token
            entries.append(self.url_result(
                url, SoundcloudIE.ie_key(), track_id, url_transparent=True, **album_info))
        return self.playlist_result(
            entries, playlist_id,
            playlist.get('title'),
            playlist.get('description'),
            **album_info,
            **traverse_obj(playlist, {
                'uploader': ('user', 'username', {str}),
                'uploader_id': ('user', 'id', {str_or_none}),
            }),
        )