def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        host = mobj.group('host') or mobj.group('host_2')
        video_id = mobj.group('id')

        video = self._call_api(
            host, video_id, '', note='Downloading video JSON')

        title = video['name']

        formats, is_live = [], False
        files = video.get('files') or []
        for playlist in (video.get('streamingPlaylists') or []):
            if not isinstance(playlist, dict):
                continue
            if playlist_url := url_or_none(playlist.get('playlistUrl')):
                is_live = True
                formats.extend(self._extract_m3u8_formats(
                    playlist_url, video_id, fatal=False, live=True))
            playlist_files = playlist.get('files')
            if not (playlist_files and isinstance(playlist_files, list)):
                continue
            files.extend(playlist_files)
        for file_ in files:
            if not isinstance(file_, dict):
                continue
            file_url = url_or_none(file_.get('fileUrl'))
            if not file_url:
                continue
            file_size = int_or_none(file_.get('size'))
            format_id = try_get(
                file_, lambda x: x['resolution']['label'], str)
            f = parse_resolution(format_id)
            f.update({
                'url': file_url,
                'format_id': format_id,
                'filesize': file_size,
            })
            if format_id == '0p':
                f['vcodec'] = 'none'
            else:
                f['fps'] = int_or_none(file_.get('fps'))
            is_live = False
            formats.append(f)

        description = video.get('description')
        if description and len(description) >= 250:
            # description is shortened
            full_description = self._call_api(
                host, video_id, 'description', note='Downloading description JSON',
                fatal=False)

            if isinstance(full_description, dict):
                description = str_or_none(full_description.get('description')) or description

        subtitles = self.extract_subtitles(host, video_id)

        def data(section, field, type_):
            return try_get(video, lambda x: x[section][field], type_)

        def account_data(field, type_):
            return data('account', field, type_)

        def channel_data(field, type_):
            return data('channel', field, type_)

        category = data('category', 'label', str)
        categories = [category] if category else None

        nsfw = video.get('nsfw')
        if nsfw is bool:
            age_limit = 18 if nsfw else 0
        else:
            age_limit = None

        webpage_url = f'https://{host}/videos/watch/{video_id}'

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': urljoin(webpage_url, video.get('thumbnailPath')),
            'timestamp': unified_timestamp(video.get('publishedAt')),
            'uploader': account_data('displayName', str),
            'uploader_id': str_or_none(account_data('id', int)),
            'uploader_url': url_or_none(account_data('url', str)),
            'channel': channel_data('displayName', str),
            'channel_id': str_or_none(channel_data('id', int)),
            'channel_url': url_or_none(channel_data('url', str)),
            'language': data('language', 'id', str),
            'license': data('licence', 'label', str),
            'duration': int_or_none(video.get('duration')),
            'view_count': int_or_none(video.get('views')),
            'like_count': int_or_none(video.get('likes')),
            'dislike_count': int_or_none(video.get('dislikes')),
            'age_limit': age_limit,
            'tags': try_get(video, lambda x: x['tags'], list),
            'categories': categories,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            'webpage_url': webpage_url,
        }