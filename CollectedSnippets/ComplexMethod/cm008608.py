def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        movie = mobj.group('movie')
        uploader_id = mobj.group('company')

        webpage = self._download_webpage(url, movie)
        film_id = self._search_regex(r"FilmId\s*=\s*'(\d+)'", webpage, 'film id')
        film_data = self._download_json(
            f'http://trailers.apple.com/trailers/feeds/data/{film_id}.json',
            film_id, fatal=False)

        if film_data:
            entries = []
            for clip in film_data.get('clips', []):
                clip_title = clip['title']

                formats = []
                for version, version_data in clip.get('versions', {}).items():
                    for size, size_data in version_data.get('sizes', {}).items():
                        src = size_data.get('src')
                        if not src:
                            continue
                        formats.append({
                            'format_id': f'{version}-{size}',
                            'url': re.sub(r'_(\d+p\.mov)', r'_h\1', src),
                            'width': int_or_none(size_data.get('width')),
                            'height': int_or_none(size_data.get('height')),
                            'language': version[:2],
                        })

                entries.append({
                    'id': movie + '-' + re.sub(r'[^a-zA-Z0-9]', '', clip_title).lower(),
                    'formats': formats,
                    'title': clip_title,
                    'thumbnail': clip.get('screen') or clip.get('thumb'),
                    'duration': parse_duration(clip.get('runtime') or clip.get('faded')),
                    'upload_date': unified_strdate(clip.get('posted')),
                    'uploader_id': uploader_id,
                })

            page_data = film_data.get('page', {})
            return self.playlist_result(entries, film_id, page_data.get('movie_title'))

        playlist_url = urllib.parse.urljoin(url, 'includes/playlists/itunes.inc')

        def fix_html(s):
            s = re.sub(r'(?s)<script[^<]*?>.*?</script>', '', s)
            s = re.sub(r'<img ([^<]*?)/?>', r'<img \1/>', s)
            # The ' in the onClick attributes are not escaped, it couldn't be parsed
            # like: http://trailers.apple.com/trailers/wb/gravity/

            def _clean_json(m):
                return 'iTunes.playURL({});'.format(m.group(1).replace('\'', '&#39;'))
            s = re.sub(self._JSON_RE, _clean_json, s)
            return f'<html>{s}</html>'
        doc = self._download_xml(playlist_url, movie, transform_source=fix_html)

        playlist = []
        for li in doc.findall('./div/ul/li'):
            on_click = li.find('.//a').attrib['onClick']
            trailer_info_json = self._search_regex(self._JSON_RE,
                                                   on_click, 'trailer info')
            trailer_info = json.loads(trailer_info_json)
            first_url = trailer_info.get('url')
            if not first_url:
                continue
            title = trailer_info['title']
            video_id = movie + '-' + re.sub(r'[^a-zA-Z0-9]', '', title).lower()
            thumbnail = li.find('.//img').attrib['src']
            upload_date = trailer_info['posted'].replace('-', '')

            runtime = trailer_info['runtime']
            m = re.search(r'(?P<minutes>[0-9]+):(?P<seconds>[0-9]{1,2})', runtime)
            duration = None
            if m:
                duration = 60 * int(m.group('minutes')) + int(m.group('seconds'))

            trailer_id = first_url.split('/')[-1].rpartition('_')[0].lower()
            settings_json_url = urllib.parse.urljoin(url, f'includes/settings/{trailer_id}.json')
            settings = self._download_json(settings_json_url, trailer_id, 'Downloading settings json')

            formats = []
            for fmt in settings['metadata']['sizes']:
                # The src is a file pointing to the real video file
                format_url = re.sub(r'_(\d*p\.mov)', r'_h\1', fmt['src'])
                formats.append({
                    'url': format_url,
                    'format': fmt['type'],
                    'width': int_or_none(fmt['width']),
                    'height': int_or_none(fmt['height']),
                })

            playlist.append({
                '_type': 'video',
                'id': video_id,
                'formats': formats,
                'title': title,
                'duration': duration,
                'thumbnail': thumbnail,
                'upload_date': upload_date,
                'uploader_id': uploader_id,
                'http_headers': {
                    'User-Agent': 'QuickTime compatible (yt-dlp)',
                },
            })

        return {
            '_type': 'playlist',
            'id': movie,
            'entries': playlist,
        }