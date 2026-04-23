def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        show_id, season_id = re.match(self._VALID_URL, url).groups()

        data = {}
        if season_id:
            data['season'] = season_id
            show_id = smuggled_data.get('show_id')
            if show_id is None:
                season = self._download_json(
                    'http://admin.mangomolo.com/analytics/index.php/plus/season_info?id=%s' % season_id,
                    season_id, headers={'Origin': 'http://awaan.ae'})
                show_id = season['id']
        data['show_id'] = show_id
        show = self._download_json(
            'http://admin.mangomolo.com/analytics/index.php/plus/show',
            show_id, data=urlencode_postdata(data), headers={
                'Origin': 'http://awaan.ae',
                'Content-Type': 'application/x-www-form-urlencoded'
            })
        if not season_id:
            season_id = show['default_season']
        for season in show['seasons']:
            if season['id'] == season_id:
                title = season.get('title_en') or season['title_ar']

                entries = []
                for video in show['videos']:
                    video_id = compat_str(video['id'])
                    entries.append(self.url_result(
                        'http://awaan.ae/media/%s' % video_id, 'AWAANVideo', video_id))

                return self.playlist_result(entries, season_id, title)