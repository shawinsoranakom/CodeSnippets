def _real_extract(self, url):
        playlist_id = self._match_id(url)
        if playlist_id.endswith('/'):
            playlist_id = playlist_id[:-1]

        webpage = self._download_webpage(url, playlist_id)

        static_assets_base = self._search_regex(r'(/_nuxt/static/\d+)', webpage, 'staticAssetsBase')
        static_assets_base = f'https://sovietscloset.com{static_assets_base}'

        sovietscloset = self.parse_nuxt_jsonp(f'{static_assets_base}/payload.js', playlist_id, 'global')['games']

        if '/' in playlist_id:
            game_slug, category_slug = playlist_id.lower().split('/')
        else:
            game_slug = playlist_id.lower()
            category_slug = 'misc'

        game = next(game for game in sovietscloset if game['slug'].lower() == game_slug)
        category = next((cat for cat in game['subcategories'] if cat.get('slug', '').lower() == category_slug),
                        game['subcategories'][0])
        category_slug = category.get('slug', '').lower() or category_slug
        playlist_title = game.get('name') or game_slug
        if category_slug != 'misc':
            playlist_title += f' - {category.get("name") or category_slug}'
        entries = [{
            **self.url_result(f'https://sovietscloset.com/video/{stream["id"]}', ie=SovietsClosetIE.ie_key()),
            **self.video_meta(
                video_id=stream['id'], game_name=game['name'], category_name=category.get('name'),
                episode_number=i + 1, stream_date=stream.get('date')),
        } for i, stream in enumerate(category['streams'])]

        return self.playlist_result(entries, playlist_id, playlist_title)