def _extract_track(self, track, track_id=None):
        track_name = track.get('songName') or track.get('name') or track['subName']
        artist = track.get('artist') or track.get('artist_name') or track.get('singers')
        title = '%s - %s' % (artist, track_name) if artist else track_name
        track_url = self._decrypt(track['location'])

        subtitles = {}
        lyrics_url = track.get('lyric_url') or track.get('lyric')
        if lyrics_url and lyrics_url.startswith('http'):
            subtitles['origin'] = [{'url': lyrics_url}]

        return {
            'id': track.get('song_id') or track_id,
            'url': track_url,
            'title': title,
            'thumbnail': track.get('pic') or track.get('album_pic'),
            'duration': int_or_none(track.get('length')),
            'creator': track.get('artist', '').split(';')[0],
            'track': track_name,
            'track_number': int_or_none(track.get('track')),
            'album': track.get('album_name') or track.get('title'),
            'artist': artist,
            'subtitles': subtitles,
        }