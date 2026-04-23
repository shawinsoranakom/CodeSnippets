def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        fn = urllib.parse.unquote(url_basename(url))
        title = os.path.splitext(fn)[0]
        content_id = None

        for part in self._yield_decoded_parts(webpage):
            if '/sm/password' in part:
                content_id = self._search_regex(r'content_id=([\w.+=/-]+)', part, 'content ID')
                break

        if content_id:
            password = self.get_param('videopassword')
            if not password:
                raise ExtractorError('Password protected video, use --video-password <password>', expected=True)

            response = self._download_json(
                'https://www.dropbox.com/sm/auth', video_id, 'POSTing video password',
                data=urlencode_postdata({
                    'is_xhr': 'true',
                    't': self._get_cookies('https://www.dropbox.com')['t'].value,
                    'content_id': content_id,
                    'password': password,
                    'url': update_url(url, scheme='', netloc=''),
                }))
            if response.get('status') != 'authed':
                raise ExtractorError('Invalid password', expected=True)

            webpage = self._download_webpage(url, video_id)

        formats, subtitles = [], {}
        has_anonymous_download = False
        thumbnail = None
        for part in self._yield_decoded_parts(webpage):
            if not has_anonymous_download:
                has_anonymous_download = self._search_regex(
                    r'(anonymous:\tanonymous)', part, 'anonymous', default=False)
            transcode_url = self._search_regex(
                r'\n.?(https://[^\x03\x08\x12\n]+\.m3u8)', part, 'transcode url', default=None)
            if not transcode_url:
                continue
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(transcode_url, video_id, 'mp4')
            thumbnail = self._search_regex(
                r'(https://www\.dropbox\.com/temp_thumb_from_token/[\w/?&=]+)', part, 'thumbnail', default=None)
            break

        # downloads enabled we can get the original file
        if has_anonymous_download:
            formats.append({
                'url': update_url_query(url, {'dl': '1'}),
                'format_id': 'original',
                'format_note': 'Original',
                'quality': 1,
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail,
        }