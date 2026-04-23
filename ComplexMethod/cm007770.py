def _extract_track(t, fatal=True):
        audio_url = t['URL'] if fatal else t.get('URL')
        if not audio_url:
            return

        audio_id = t['File'] if fatal else t.get('File')
        if not audio_id:
            return

        thumbnail = t.get('AlbumCoverURL') or t.get('FiledAlbumCover')
        uploader = t.get('OwnerName') or t.get('OwnerName_Text_HTML')
        uploader_id = t.get('UploaderID')
        duration = int_or_none(t.get('DurationInSeconds')) or parse_duration(
            t.get('Duration') or t.get('DurationStr'))
        view_count = int_or_none(t.get('PlayCount') or t.get('PlayCount_hr'))

        track = t.get('Name') or t.get('Name_Text_HTML')
        artist = t.get('Author') or t.get('Author_Text_HTML')

        if track:
            title = '%s - %s' % (artist, track) if artist else track
        else:
            title = audio_id

        return {
            'extractor_key': MailRuMusicIE.ie_key(),
            'id': audio_id,
            'title': title,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'duration': duration,
            'view_count': view_count,
            'vcodec': 'none',
            'abr': int_or_none(t.get('BitRate')),
            'track': track,
            'artist': artist,
            'album': t.get('Album'),
            'url': audio_url,
        }