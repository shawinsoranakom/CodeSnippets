def _real_extract(self, url):
        series_slug, season_id = re.match(self._VALID_URL, url).groups()

        series = self._download_json(
            'https://api.svt.se/contento/graphql', series_slug,
            'Downloading series page', query={
                'query': '''{
  listablesBySlug(slugs: ["%s"]) {
    associatedContent(include: [productionPeriod, season]) {
      items {
        item {
          ... on Episode {
            videoSvtId
          }
        }
      }
      id
      name
    }
    id
    longDescription
    name
    shortDescription
  }
}''' % series_slug,
            })['data']['listablesBySlug'][0]

        season_name = None

        entries = []
        for season in series['associatedContent']:
            if not isinstance(season, dict):
                continue
            if season_id:
                if season.get('id') != season_id:
                    continue
                season_name = season.get('name')
            items = season.get('items')
            if not isinstance(items, list):
                continue
            for item in items:
                video = item.get('item') or {}
                content_id = video.get('videoSvtId')
                if not content_id or not isinstance(content_id, compat_str):
                    continue
                entries.append(self.url_result(
                    'svt:' + content_id, SVTPlayIE.ie_key(), content_id))

        title = series.get('name')
        season_name = season_name or season_id

        if title and season_name:
            title = '%s - %s' % (title, season_name)
        elif season_id:
            title = season_id

        return self.playlist_result(
            entries, season_id or series.get('id'), title,
            dict_get(series, ('longDescription', 'shortDescription')))