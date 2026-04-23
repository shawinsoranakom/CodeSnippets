def _entries(self, show_name):
        headers = {
            'x-disco-client': self._X_CLIENT,
            'x-disco-params': f'realm={self._REALM}',
            'referer': self._DOMAIN,
            'Authentication': self._get_auth(self._BASE_API, None, self._REALM),
        }
        show_json = self._download_json(
            f'{self._BASE_API}cms/routes/{self._SHOW_STR}/{show_name}?include=default',
            video_id=show_name, headers=headers)['included'][self._INDEX]['attributes']['component']
        show_id = show_json['mandatoryParams'].split('=')[-1]
        season_url = self._BASE_API + 'content/videos?sort=episodeNumber&filter[seasonNumber]={}&filter[show.id]={}&page[size]=100&page[number]={}'
        for season in show_json['filters'][0]['options']:
            season_id = season['id']
            total_pages, page_num = 1, 0
            while page_num < total_pages:
                season_json = self._download_json(
                    season_url.format(season_id, show_id, str(page_num + 1)), show_name, headers=headers,
                    note='Downloading season {} JSON metadata{}'.format(season_id, f' page {page_num}' if page_num else ''))
                if page_num == 0:
                    total_pages = try_get(season_json, lambda x: x['meta']['totalPages'], int) or 1
                episodes_json = season_json['data']
                for episode in episodes_json:
                    video_path = episode['attributes']['path']
                    yield self.url_result(
                        f'{self._DOMAIN}videos/{video_path}',
                        ie=self._VIDEO_IE.ie_key(), video_id=episode.get('id') or video_path)
                page_num += 1