def _real_extract(self, url):
        site, serie_kind, series_id = self._match_valid_url(url).groups()
        is_radio = site == 'radio.nrk'
        domain = 'radio' if is_radio else 'tv'

        size_prefix = 'p' if is_radio else 'embeddedInstalmentsP'
        series = self._call_api(
            f'{domain}/catalog/{self._catalog_name(serie_kind)}/{series_id}',
            series_id, 'serie', query={size_prefix + 'ageSize': 50})
        titles = try_get(series, [
            lambda x: x['titles'],
            lambda x: x[x['type']]['titles'],
            lambda x: x[x['seriesType']]['titles'],
        ]) or {}

        entries = []
        entries.extend(self._entries(series, series_id))
        embedded = series.get('_embedded') or {}
        linked_seasons = try_get(series, lambda x: x['_links']['seasons']) or []
        embedded_seasons = embedded.get('seasons') or []
        if len(linked_seasons) > len(embedded_seasons):
            for season in linked_seasons:
                season_url = urljoin(url, season.get('href'))
                if not season_url:
                    season_name = season.get('name')
                    if season_name and isinstance(season_name, str):
                        season_url = f'https://{domain}.nrk.no/serie/{series_id}/sesong/{season_name}'
                if season_url:
                    entries.append(self.url_result(
                        season_url, ie=NRKTVSeasonIE.ie_key(),
                        video_title=season.get('title')))
        else:
            for season in embedded_seasons:
                entries.extend(self._entries(season, series_id))
        entries.extend(self._entries(
            embedded.get('extraMaterial') or {}, series_id))

        return self.playlist_result(
            entries, series_id, titles.get('title'), titles.get('subtitle'))