def _extract_set(self, playlist, token=None):
        playlist_id = compat_str(playlist['id'])
        tracks = playlist.get('tracks') or []
        if not all([t.get('permalink_url') for t in tracks]) and token:
            tracks = self._download_json(
                self._API_V2_BASE + 'tracks', playlist_id,
                'Downloading tracks', query={
                    'ids': ','.join([compat_str(t['id']) for t in tracks]),
                    'playlistId': playlist_id,
                    'playlistSecretToken': token,
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
                url, SoundcloudIE.ie_key(), track_id))
        return self.playlist_result(
            entries, playlist_id,
            playlist.get('title'),
            playlist.get('description'))