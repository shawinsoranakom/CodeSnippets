def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        json_data = self._parse_json(self._search_regex(
            r'<script[^>]+type="text/json"[^>]*>\s*({[^>]+})', webpage, 'json'),
            display_id)

        title = json_data['title']
        formats = []

        video_id = None

        for key in ('file', 'audio', 'video', 'high_res_video'):
            media_url = json_data.get(key, '')
            if not media_url:
                continue
            media_url = re.sub(r'\?.*', '', urllib.parse.urljoin(url, media_url))
            video_id = video_id or remove_start(os.path.splitext(url_basename(media_url))[0], 'dn')
            formats.append({
                'url': media_url,
                'vcodec': 'none' if key == 'audio' else None,
            })

        default_lang = 'en'
        subtitles = {}

        def add_subtitle_item(lang, info_dict):
            if lang not in subtitles:
                subtitles[lang] = []
            subtitles[lang].append(info_dict)

        # chapter_file are not subtitles
        if 'caption_file' in json_data:
            add_subtitle_item(default_lang, {
                'url': urllib.parse.urljoin(url, json_data['caption_file']),
            })

        for subtitle_item in json_data.get('captions', []):
            lang = subtitle_item.get('language', '').lower() or default_lang
            add_subtitle_item(lang, {
                'url': urllib.parse.urljoin(url, subtitle_item['url']),
            })

        description = self._og_search_description(webpage, default=None)

        return {
            'id': video_id or display_id,
            'title': title,
            'description': description,
            'thumbnail': json_data.get('image'),
            'subtitles': subtitles,
            'formats': formats,
        }