def _real_extract(self, url):
        query = parse_qs(url)
        video_id = traverse_obj(query, (
            ('show', 'id'), 0, {int_or_none}, filter, {str_or_none}), get_all=False)
        webpage = self._download_webpage(url, video_id)

        player_data, media_data = self._search_regex(
            r'LR\.audio\.Player\s*\([^{]*(?P<player>\{.*?\}),(?P<media>\{.*\})\);',
            webpage, 'player json', group=('player', 'media'))

        player_json = self._parse_json(
            player_data, video_id, transform_source=js_to_json, fatal=False) or {}
        media_json = self._parse_json(media_data, video_id, transform_source=js_to_json)

        entries = []
        for item in traverse_obj(media_json, (('audio', 'video'), lambda _, v: v['id'])):
            formats = []
            for source_url in traverse_obj(item, ('sources', ..., 'file', {url_or_none})):
                if determine_ext(source_url) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(source_url, video_id, fatal=False))
                else:
                    formats.append({'url': source_url})

            id_ = item['id']
            title = item.get('title')
            if id_.startswith('v') and not title:
                title = traverse_obj(
                    media_json, ('audio', lambda _, v: v['id'][1:] == id_[1:], 'title',
                                 {lambda x: x and f'{x} - Video Version'}), get_all=False)

            entries.append({
                'formats': formats,
                'thumbnail': urljoin(url, player_json.get('poster')),
                'id': id_,
                'title': title,
                'duration': traverse_obj(item, ('duration', {int_or_none})),
            })

        if len(entries) == 1:
            return entries[0]

        return self.playlist_result(entries, video_id)