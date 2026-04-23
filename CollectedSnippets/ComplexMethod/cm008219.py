def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        for message in [
            'Debido a tu ubicación no puedes ver el contenido',
            'You are not allowed to watch this video: Geo Fencing Restriction',
            'Este contenido no está disponible en tu zona geográfica.',
            'El contenido sólo está disponible dentro de',
        ]:
            if message in webpage:
                self.raise_geo_restricted()

        player_config = self._search_json(r'window\.MDSTRM\.OPTIONS\s*=', webpage, 'metadata', video_id)

        formats, subtitles = [], {}
        for video_format in player_config['src']:
            if video_format == 'hls':
                params = {
                    'at': 'web-app',
                    'access_token': traverse_obj(parse_qs(url), ('access_token', 0)),
                }
                for name, key in (('MDSTRMUID', 'uid'), ('MDSTRMSID', 'sid'), ('MDSTRMPID', 'pid'), ('VERSION', 'av')):
                    params[key] = self._search_regex(
                        rf'window\.{name}\s*=\s*["\']([^"\']+)["\'];', webpage, key, default=None)

                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    update_url_query(player_config['src'][video_format], filter_dict(params)), video_id)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif video_format == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(player_config['src'][video_format], video_id)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                formats.append({
                    'url': player_config['src'][video_format],
                })

        return {
            'id': video_id,
            'title': self._og_search_title(webpage) or player_config.get('title'),
            'description': self._og_search_description(webpage),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': player_config.get('type') == 'live',
            'thumbnail': self._og_search_thumbnail(webpage),
        }