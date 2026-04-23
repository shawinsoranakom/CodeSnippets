def _real_extract(self, url):
        playlist_id = self._match_id(url)
        data_json = self._download_json(
            f'https://www.musicdex.org/secure/albums/{playlist_id}?defaultRelations=true', playlist_id)['album']
        entries = [self._return_info(track, data_json, track['id'])
                   for track in data_json.get('tracks') or [] if track.get('id')]

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': data_json.get('name'),
            'description': data_json.get('description'),
            'genres': [genre.get('name') for genre in data_json.get('genres') or []],
            'view_count': data_json.get('plays'),
            'artists': [artist.get('name') for artist in data_json.get('artists') or []],
            'thumbnail': format_field(data_json, 'image', 'https://www.musicdex.org/%s'),
            'release_year': try_get(data_json, lambda x: date_from_str(unified_strdate(x['release_date'])).year),
            'entries': entries,
        }