def _extract_tracks(self, source, item_id, url, tld):
        tracks = source['tracks']
        track_ids = [str(track_id) for track_id in source['trackIds']]

        # tracks dictionary shipped with playlist.jsx API is limited to 150 tracks,
        # missing tracks should be retrieved manually.
        if len(tracks) < len(track_ids):
            present_track_ids = {
                str(track['id'])
                for track in tracks if track.get('id')}
            missing_track_ids = [
                track_id for track_id in track_ids
                if track_id not in present_track_ids]
            # Request missing tracks in chunks to avoid exceeding max HTTP header size,
            # see https://github.com/ytdl-org/youtube-dl/issues/27355
            _TRACKS_PER_CHUNK = 250
            for chunk_num in itertools.count(0):
                start = chunk_num * _TRACKS_PER_CHUNK
                end = start + _TRACKS_PER_CHUNK
                missing_track_ids_req = missing_track_ids[start:end]
                assert missing_track_ids_req
                missing_tracks = self._call_api(
                    'track-entries', tld, url, item_id,
                    f'Downloading missing tracks JSON chunk {chunk_num + 1}', {
                        'entries': ','.join(missing_track_ids_req),
                        'lang': tld,
                        'external-domain': f'music.yandex.{tld}',
                        'overembed': 'false',
                        'strict': 'true',
                    })
                if missing_tracks:
                    tracks.extend(missing_tracks)
                if end >= len(missing_track_ids):
                    break

        return tracks