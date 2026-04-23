def _real_extract(self, url):
        content_path, rss = re.match(self._VALID_URL, url).groups()

        if rss:
            return self._extract_list(content_path, url)

        webpage = self._download_webpage(
            url, content_path, 'Downloading web page')

        episode_data = self._search_regex(
            r"data-episode='([^']+)'", webpage, 'episode data', default=None)
        if episode_data:
            episode_data = self._parse_json(unescapeHTML(
                episode_data), content_path)
            content_id = episode_data['contentId']
            is_session = '/Sessions(' in episode_data['api']
            content_url = 'https://channel9.msdn.com/odata' + episode_data['api'] + '?$select=Captions,CommentCount,MediaLengthInSeconds,PublishedDate,Rating,RatingCount,Title,VideoMP4High,VideoMP4Low,VideoMP4Medium,VideoPlayerPreviewImage,VideoWMV,VideoWMVHQ,Views,'
            if is_session:
                content_url += 'Code,Description,Room,Slides,Speakers,ZipFile&$expand=Speakers'
            else:
                content_url += 'Authors,Body&$expand=Authors'
            content_data = self._download_json(content_url, content_id)
            title = content_data['Title']

            QUALITIES = (
                'mp3',
                'wmv', 'mp4',
                'wmv-low', 'mp4-low',
                'wmv-mid', 'mp4-mid',
                'wmv-high', 'mp4-high',
            )

            quality_key = qualities(QUALITIES)

            def quality(quality_id, format_url):
                return (len(QUALITIES) if '_Source.' in format_url
                        else quality_key(quality_id))

            formats = []
            urls = set()

            SITE_QUALITIES = {
                'MP3': 'mp3',
                'MP4': 'mp4',
                'Low Quality WMV': 'wmv-low',
                'Low Quality MP4': 'mp4-low',
                'Mid Quality WMV': 'wmv-mid',
                'Mid Quality MP4': 'mp4-mid',
                'High Quality WMV': 'wmv-high',
                'High Quality MP4': 'mp4-high',
            }

            formats_select = self._search_regex(
                r'(?s)<select[^>]+name=["\']format[^>]+>(.+?)</select', webpage,
                'formats select', default=None)
            if formats_select:
                for mobj in re.finditer(
                        r'<option\b[^>]+\bvalue=(["\'])(?P<url>(?:(?!\1).)+)\1[^>]*>\s*(?P<format>[^<]+?)\s*<',
                        formats_select):
                    format_url = mobj.group('url')
                    if format_url in urls:
                        continue
                    urls.add(format_url)
                    format_id = mobj.group('format')
                    quality_id = SITE_QUALITIES.get(format_id, format_id)
                    formats.append({
                        'url': format_url,
                        'format_id': quality_id,
                        'quality': quality(quality_id, format_url),
                        'vcodec': 'none' if quality_id == 'mp3' else None,
                    })

            API_QUALITIES = {
                'VideoMP4Low': 'mp4-low',
                'VideoWMV': 'wmv-mid',
                'VideoMP4Medium': 'mp4-mid',
                'VideoMP4High': 'mp4-high',
                'VideoWMVHQ': 'wmv-hq',
            }

            for format_id, q in API_QUALITIES.items():
                q_url = content_data.get(format_id)
                if not q_url or q_url in urls:
                    continue
                urls.add(q_url)
                formats.append({
                    'url': q_url,
                    'format_id': q,
                    'quality': quality(q, q_url),
                })

            self._sort_formats(formats)

            slides = content_data.get('Slides')
            zip_file = content_data.get('ZipFile')

            if not formats and not slides and not zip_file:
                raise ExtractorError(
                    'None of recording, slides or zip are available for %s' % content_path)

            subtitles = {}
            for caption in content_data.get('Captions', []):
                caption_url = caption.get('Url')
                if not caption_url:
                    continue
                subtitles.setdefault(caption.get('Language', 'en'), []).append({
                    'url': caption_url,
                    'ext': 'vtt',
                })

            common = {
                'id': content_id,
                'title': title,
                'description': clean_html(content_data.get('Description') or content_data.get('Body')),
                'thumbnail': content_data.get('VideoPlayerPreviewImage'),
                'duration': int_or_none(content_data.get('MediaLengthInSeconds')),
                'timestamp': parse_iso8601(content_data.get('PublishedDate')),
                'avg_rating': int_or_none(content_data.get('Rating')),
                'rating_count': int_or_none(content_data.get('RatingCount')),
                'view_count': int_or_none(content_data.get('Views')),
                'comment_count': int_or_none(content_data.get('CommentCount')),
                'subtitles': subtitles,
            }
            if is_session:
                speakers = []
                for s in content_data.get('Speakers', []):
                    speaker_name = s.get('FullName')
                    if not speaker_name:
                        continue
                    speakers.append(speaker_name)

                common.update({
                    'session_code': content_data.get('Code'),
                    'session_room': content_data.get('Room'),
                    'session_speakers': speakers,
                })
            else:
                authors = []
                for a in content_data.get('Authors', []):
                    author_name = a.get('DisplayName')
                    if not author_name:
                        continue
                    authors.append(author_name)
                common['authors'] = authors

            contents = []

            if slides:
                d = common.copy()
                d.update({'title': title + '-Slides', 'url': slides})
                contents.append(d)

            if zip_file:
                d = common.copy()
                d.update({'title': title + '-Zip', 'url': zip_file})
                contents.append(d)

            if formats:
                d = common.copy()
                d.update({'title': title, 'formats': formats})
                contents.append(d)
            return self.playlist_result(contents)
        else:
            return self._extract_list(content_path)