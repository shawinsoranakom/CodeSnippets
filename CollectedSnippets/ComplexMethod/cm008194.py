def _real_extract(self, url):
        track_id, display_id = self._match_valid_url(url).groups()
        # webpage = self._download_webpage(
        #     'https://www.jamendo.com/track/' + track_id, track_id)
        # models = self._parse_json(self._html_search_regex(
        #     r"data-bundled-models='([^']+)",
        #     webpage, 'bundled models'), track_id)
        # track = models['track']['models'][0]
        track = self._call_api('track', track_id)
        title = track_name = track['name']
        # get_model = lambda x: try_get(models, lambda y: y[x]['models'][0], dict) or {}
        # artist = get_model('artist')
        # artist_name = artist.get('name')
        # if artist_name:
        #     title = '%s - %s' % (artist_name, title)
        # album = get_model('album')
        artist = self._call_api('artist', track.get('artistId'), fatal=False)
        album = self._call_api('album', track.get('albumId'), fatal=False)

        formats = [{
            'url': f'https://{sub_domain}.jamendo.com/?trackid={track_id}&format={format_id}&from=app-97dab294',
            'format_id': format_id,
            'ext': ext,
            'quality': quality,
        } for quality, (format_id, sub_domain, ext) in enumerate((
            ('mp31', 'mp3l', 'mp3'),
            ('mp32', 'mp3d', 'mp3'),
            ('ogg1', 'ogg', 'ogg'),
            ('flac', 'flac', 'flac'),
        ))]

        urls = []
        thumbnails = []
        for covers in (track.get('cover') or {}).values():
            for cover_id, cover_url in covers.items():
                if not cover_url or cover_url in urls:
                    continue
                urls.append(cover_url)
                urlh = self._request_webpage(
                    HEADRequest(cover_url), track_id, 'Checking thumbnail extension',
                    errnote=False, fatal=False)
                if not urlh:
                    continue
                size = int_or_none(cover_id.lstrip('size'))
                thumbnails.append({
                    'id': cover_id,
                    'ext': urlhandle_detect_ext(urlh, default='jpg'),
                    'url': cover_url,
                    'width': size,
                    'height': size,
                })

        tags = []
        for tag in (track.get('tags') or []):
            tag_name = tag.get('name')
            if not tag_name:
                continue
            tags.append(tag_name)

        stats = track.get('stats') or {}
        video_license = track.get('licenseCC') or []

        return {
            'id': track_id,
            'display_id': display_id,
            'thumbnails': thumbnails,
            'title': title,
            'description': track.get('description'),
            'duration': int_or_none(track.get('duration')),
            'artist': artist.get('name'),
            'track': track_name,
            'album': album.get('name'),
            'formats': formats,
            'license': '-'.join(video_license) if video_license else None,
            'timestamp': int_or_none(track.get('dateCreated')),
            'view_count': int_or_none(stats.get('listenedAll')),
            'like_count': int_or_none(stats.get('favorited')),
            'average_rating': int_or_none(stats.get('averageNote')),
            'tags': tags,
        }