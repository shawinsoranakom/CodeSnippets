def _real_extract(self, url):
        title = self._match_id(url)
        webpage = self._download_webpage(url, title)
        tralbum = self._extract_data_attr(webpage, title)
        thumbnail = self._og_search_thumbnail(webpage)

        track_id = None
        track = None
        track_number = None
        duration = None

        formats = []
        track_info = try_get(tralbum, lambda x: x['trackinfo'][0], dict)
        if track_info:
            file_ = track_info.get('file')
            if isinstance(file_, dict):
                for format_id, format_url in file_.items():
                    if not url_or_none(format_url):
                        continue
                    ext, abr_str = format_id.split('-', 1)
                    formats.append({
                        'format_id': format_id,
                        'url': self._proto_relative_url(format_url, 'http:'),
                        'ext': ext,
                        'vcodec': 'none',
                        'acodec': ext,
                        'abr': int_or_none(abr_str),
                    })
            track = track_info.get('title')
            track_id = str_or_none(
                track_info.get('track_id') or track_info.get('id'))
            track_number = int_or_none(track_info.get('track_num'))
            duration = float_or_none(track_info.get('duration'))

        embed = self._extract_data_attr(webpage, title, 'embed', False)
        current = tralbum.get('current') or {}
        artist = embed.get('artist') or current.get('artist') or tralbum.get('artist')
        timestamp = unified_timestamp(
            current.get('publish_date') or tralbum.get('album_publish_date'))

        download_link = tralbum.get('freeDownloadPage')
        if download_link:
            track_id = compat_str(tralbum['id'])

            download_webpage = self._download_webpage(
                download_link, track_id, 'Downloading free downloads page')

            blob = self._extract_data_attr(download_webpage, track_id, 'blob')

            info = try_get(
                blob, (lambda x: x['digital_items'][0],
                       lambda x: x['download_items'][0]), dict)
            if info:
                downloads = info.get('downloads')
                if isinstance(downloads, dict):
                    if not track:
                        track = info.get('title')
                    if not artist:
                        artist = info.get('artist')
                    if not thumbnail:
                        thumbnail = info.get('thumb_url')

                    download_formats = {}
                    download_formats_list = blob.get('download_formats')
                    if isinstance(download_formats_list, list):
                        for f in blob['download_formats']:
                            name, ext = f.get('name'), f.get('file_extension')
                            if all(isinstance(x, compat_str) for x in (name, ext)):
                                download_formats[name] = ext.strip('.')

                    for format_id, f in downloads.items():
                        format_url = f.get('url')
                        if not format_url:
                            continue
                        # Stat URL generation algorithm is reverse engineered from
                        # download_*_bundle_*.js
                        stat_url = update_url_query(
                            format_url.replace('/download/', '/statdownload/'), {
                                '.rand': int(time.time() * 1000 * random.random()),
                            })
                        format_id = f.get('encoding_name') or format_id
                        stat = self._download_json(
                            stat_url, track_id, 'Downloading %s JSON' % format_id,
                            transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1],
                            fatal=False)
                        if not stat:
                            continue
                        retry_url = url_or_none(stat.get('retry_url'))
                        if not retry_url:
                            continue
                        formats.append({
                            'url': self._proto_relative_url(retry_url, 'http:'),
                            'ext': download_formats.get(format_id),
                            'format_id': format_id,
                            'format_note': f.get('description'),
                            'filesize': parse_filesize(f.get('size_mb')),
                            'vcodec': 'none',
                        })

        self._sort_formats(formats)

        title = '%s - %s' % (artist, track) if artist else track

        if not duration:
            duration = float_or_none(self._html_search_meta(
                'duration', webpage, default=None))

        return {
            'id': track_id,
            'title': title,
            'thumbnail': thumbnail,
            'uploader': artist,
            'timestamp': timestamp,
            'release_timestamp': unified_timestamp(tralbum.get('album_release_date')),
            'duration': duration,
            'track': track,
            'track_number': track_number,
            'track_id': track_id,
            'artist': artist,
            'album': embed.get('album_title'),
            'formats': formats,
        }