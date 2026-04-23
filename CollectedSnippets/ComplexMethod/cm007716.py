def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        tld, album_id, track_id = mobj.group('tld'), mobj.group('album_id'), mobj.group('id')

        track = self._call_api(
            'track', tld, url, track_id, 'Downloading track JSON',
            {'track': '%s:%s' % (track_id, album_id)})['track']
        track_title = track['title']
        track_version = track.get('version')
        if track_version:
            track_title = '%s (%s)' % (track_title, track_version)

        download_data = self._download_json(
            'https://music.yandex.ru/api/v2.1/handlers/track/%s:%s/web-album_track-track-track-main/download/m' % (track_id, album_id),
            track_id, 'Downloading track location url JSON',
            query={'hq': 1},
            headers={'X-Retpath-Y': url})

        fd_data = self._download_json(
            download_data['src'], track_id,
            'Downloading track location JSON',
            query={'format': 'json'})
        key = hashlib.md5(('XGRlBW9FXlekgbPrRHuSiA' + fd_data['path'][1:] + fd_data['s']).encode('utf-8')).hexdigest()
        f_url = 'http://%s/get-mp3/%s/%s?track-id=%s ' % (fd_data['host'], key, fd_data['ts'] + fd_data['path'], track['id'])

        thumbnail = None
        cover_uri = track.get('albums', [{}])[0].get('coverUri')
        if cover_uri:
            thumbnail = cover_uri.replace('%%', 'orig')
            if not thumbnail.startswith('http'):
                thumbnail = 'http://' + thumbnail

        track_info = {
            'id': track_id,
            'ext': 'mp3',
            'url': f_url,
            'filesize': int_or_none(track.get('fileSize')),
            'duration': float_or_none(track.get('durationMs'), 1000),
            'thumbnail': thumbnail,
            'track': track_title,
            'acodec': download_data.get('codec'),
            'abr': int_or_none(download_data.get('bitrate')),
        }

        def extract_artist_name(artist):
            decomposed = artist.get('decomposed')
            if not isinstance(decomposed, list):
                return artist['name']
            parts = [artist['name']]
            for element in decomposed:
                if isinstance(element, dict) and element.get('name'):
                    parts.append(element['name'])
                elif isinstance(element, compat_str):
                    parts.append(element)
            return ''.join(parts)

        def extract_artist(artist_list):
            if artist_list and isinstance(artist_list, list):
                artists_names = [extract_artist_name(a) for a in artist_list if a.get('name')]
                if artists_names:
                    return ', '.join(artists_names)

        albums = track.get('albums')
        if albums and isinstance(albums, list):
            album = albums[0]
            if isinstance(album, dict):
                year = album.get('year')
                disc_number = int_or_none(try_get(
                    album, lambda x: x['trackPosition']['volume']))
                track_number = int_or_none(try_get(
                    album, lambda x: x['trackPosition']['index']))
                track_info.update({
                    'album': album.get('title'),
                    'album_artist': extract_artist(album.get('artists')),
                    'release_year': int_or_none(year),
                    'genre': album.get('genre'),
                    'disc_number': disc_number,
                    'track_number': track_number,
                })

        track_artist = extract_artist(track.get('artists'))
        if track_artist:
            track_info.update({
                'artist': track_artist,
                'title': '%s - %s' % (track_artist, track_title),
            })
        else:
            track_info['title'] = track_title

        return track_info