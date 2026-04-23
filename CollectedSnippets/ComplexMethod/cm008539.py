def _build_playlist(self, tracks):
        entries = []
        for track in tracks:
            track_id = track.get('id') or track.get('realId')
            if not track_id:
                continue
            albums = track.get('albums')
            if not albums or not isinstance(albums, list):
                continue
            album = albums[0]
            if not isinstance(album, dict):
                continue
            album_id = album.get('id')
            if not album_id:
                continue
            entries.append(self.url_result(
                f'http://music.yandex.ru/album/{album_id}/track/{track_id}',
                ie=YandexMusicTrackIE.ie_key(), video_id=track_id))
        return entries