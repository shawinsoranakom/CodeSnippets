def _get_metadata_opts(self, info):
        meta_prefix = 'meta'
        metadata = collections.defaultdict(dict)

        def add(meta_list, info_list=None):
            value = next((
                info[key] for key in [f'{meta_prefix}_', *variadic(info_list or meta_list)]
                if info.get(key) is not None), None)
            if value not in ('', None):
                value = ', '.join(map(str, variadic(value)))
                value = value.replace('\0', '')  # nul character cannot be passed in command line
                metadata['common'].update(dict.fromkeys(variadic(meta_list), value))

        # Info on media metadata/metadata supported by ffmpeg:
        # https://wiki.multimedia.cx/index.php/FFmpeg_Metadata
        # https://kdenlive.org/en/project/adding-meta-data-to-mp4-video/
        # https://kodi.wiki/view/Video_file_tagging

        add('title', ('track', 'title'))
        add('date', 'upload_date')
        add(('description', 'synopsis'), 'description')
        add(('purl', 'comment'), 'webpage_url')
        add('track', 'track_number')
        add('artist', ('artist', 'artists', 'creator', 'creators', 'uploader', 'uploader_id'))
        add('composer', ('composer', 'composers'))
        add('genre', ('genre', 'genres', 'categories', 'tags'))
        add('album', ('album', 'series'))
        add('album_artist', ('album_artist', 'album_artists'))
        add('disc', 'disc_number')
        add('show', 'series')
        add('season_number')
        add('episode_id', ('episode', 'episode_id'))
        add('episode_sort', 'episode_number')
        if 'embed-metadata' in self.get_param('compat_opts', []):
            add('comment', 'description')
            metadata['common'].pop('synopsis', None)

        meta_regex = rf'{re.escape(meta_prefix)}(?P<i>\d+)?_(?P<key>.+)'
        for key, value in info.items():
            mobj = re.fullmatch(meta_regex, key)
            if value is not None and mobj:
                metadata[mobj.group('i') or 'common'][mobj.group('key')] = value.replace('\0', '')

        # Write id3v1 metadata also since Windows Explorer can't handle id3v2 tags
        yield ('-write_id3v1', '1')

        for name, value in metadata['common'].items():
            yield ('-metadata', f'{name}={value}')

        stream_idx = 0
        for fmt in info.get('requested_formats') or [info]:
            stream_count = 2 if 'none' not in (fmt.get('vcodec'), fmt.get('acodec')) else 1
            lang = ISO639Utils.short2long(fmt.get('language') or '') or fmt.get('language')
            for i in range(stream_idx, stream_idx + stream_count):
                if lang:
                    metadata[str(i)].setdefault('language', lang)
                for name, value in metadata[str(i)].items():
                    yield (f'-metadata:s:{i}', f'{name}={value}')
            stream_idx += stream_count