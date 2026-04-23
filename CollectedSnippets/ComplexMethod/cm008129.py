def _real_extract(self, url):
        video_id = urllib.parse.unquote_plus(self._match_id(url))
        identifier, _, entry_id = video_id.partition('/')

        # Archive.org metadata API doesn't clearly demarcate playlist entries
        # or subtitle tracks, so we get them from the embeddable player.
        embed_page = self._download_webpage(f'https://archive.org/embed/{identifier}', identifier)
        playlist = self._playlist_data(embed_page)

        entries = {}
        for p in playlist:
            # If the user specified a playlist entry in the URL, ignore the
            # rest of the playlist.
            if entry_id and p['orig'] != entry_id:
                continue

            entries[p['orig']] = {
                'formats': [],
                'thumbnails': [],
                'artist': p.get('artist'),
                'track': p.get('title'),
                'subtitles': {},
            }

            for track in p.get('tracks', []):
                if track['kind'] != 'subtitles':
                    continue
                entries[p['orig']][track['label']] = {
                    'url': 'https://archive.org/' + track['file'].lstrip('/'),
                }

        metadata = self._download_json(f'https://archive.org/metadata/{identifier}', identifier)
        m = metadata['metadata']
        identifier = m['identifier']

        info = traverse_obj(m, {
            'title': ('title', {str}),
            'description': ('description', ({str}, (..., all, {' '.join})), {clean_html}, filter, any),
            'uploader': (('uploader', 'adder'), {str}, any),
            'creators': ('creator', (None, ...), {str}, filter, all, filter),
            'license': ('licenseurl', {url_or_none}),
            'release_date': ('date', {unified_strdate}),
            'timestamp': (('publicdate', 'addeddate'), {unified_timestamp}, any),
            'location': ('venue', {str}),
            'release_year': ('year', {int_or_none}),
        })
        info.update({
            'id': identifier,
            'webpage_url': f'https://archive.org/details/{identifier}',
        })

        for f in metadata['files']:
            if f['name'] in entries:
                entries[f['name']] = merge_dicts(entries[f['name']], {
                    'id': identifier + '/' + f['name'],
                    **traverse_obj(f, {
                        'title': (('title', 'name'), {str}, any),
                        'display_id': ('name', {str}),
                        'description': ('description', ({str}, (..., all, {' '.join})), {clean_html}, filter, any),
                        'creators': ('creator', (None, ...), {str}, filter, all, filter),
                        'duration': ('length', {parse_duration}),
                        'track_number': ('track', {int_or_none}),
                        'album': ('album', {str}),
                        'discnumber': ('disc', {int_or_none}),
                        'release_year': ('year', {int_or_none}),
                    }),
                })
                entry = entries[f['name']]
            elif traverse_obj(f, ('original', {str})) in entries:
                entry = entries[f['original']]
            else:
                continue

            if f.get('format') == 'Thumbnail':
                entry['thumbnails'].append({
                    'id': f['name'],
                    'url': 'https://archive.org/download/' + identifier + '/' + f['name'],
                    'width': int_or_none(f.get('width')),
                    'height': int_or_none(f.get('width')),
                    'filesize': int_or_none(f.get('size'))})

            _, has_ext, extension = f['name'].rpartition('.')
            if not has_ext:
                extension = None

            # We don't want to skip private formats if the user has access to them,
            # however without access to an account with such privileges we can't implement/test this.
            # For now to be safe, we will only skip them if there is no user logged in.
            is_logged_in = bool(self._get_cookies('https://archive.org').get('logged-in-sig'))
            if extension in KNOWN_EXTENSIONS and (not f.get('private') or is_logged_in):
                entry['formats'].append({
                    'url': 'https://archive.org/download/' + identifier + '/' + urllib.parse.quote(f['name']),
                    'format': f.get('format'),
                    'width': int_or_none(f.get('width')),
                    'height': int_or_none(f.get('height')),
                    'filesize': int_or_none(f.get('size')),
                    'protocol': 'https',
                    'source_preference': 0 if f.get('source') == 'original' else -1,
                    'format_note': f.get('source'),
                })

        for entry in entries.values():
            entry['_format_sort_fields'] = ('source', )

        if len(entries) == 1:
            # If there's only one item, use it as the main info dict
            only_video = next(iter(entries.values()))
            if entry_id:
                info = merge_dicts(only_video, info)
            else:
                info = merge_dicts(info, only_video)
        else:
            # Otherwise, we have a playlist.
            info['_type'] = 'playlist'
            info['entries'] = list(entries.values())

        if metadata.get('reviews'):
            info['comments'] = []
            for review in metadata['reviews']:
                info['comments'].append({
                    'id': review.get('review_id'),
                    'author': review.get('reviewer'),
                    'text': join_nonempty('reviewtitle', 'reviewbody', from_dict=review, delim='\n\n'),
                    'timestamp': unified_timestamp(review.get('createdate')),
                    'parent': 'root'})

        return info