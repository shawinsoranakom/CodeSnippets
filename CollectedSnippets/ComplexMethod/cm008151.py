def _real_extract(self, url):
        display_id = self._match_id(url)
        data = self._download_json(
            f'https://production-n.toggo.de/api/assetstore/vod/asset/{display_id}', display_id)['data']

        brightcove_id = next(
            x['value'] for x in data['custom_fields'] if x.get('key') == 'video-cloud-id')
        info = self._downloader.get_info_extractor('BrightcoveNew').extract(
            f'http://players.brightcove.net/6057955896001/default_default/index.html?videoId={brightcove_id}')

        for f in info['formats']:
            if '/dash/live/cenc/' in f.get('fragment_base_url', ''):
                # Get hidden non-DRM format
                f['fragment_base_url'] = f['fragment_base_url'].replace('/cenc/', '/clear/')
                f['has_drm'] = False

            if '/fairplay/' in f.get('manifest_url', ''):
                f['has_drm'] = True

        thumbnails = [{
            'id': name,
            'url': url,
            'width': int_or_none(next(iter(parse_qs(url).get('width', [])), None)),
        } for name, url in (data.get('images') or {}).items()]

        return {
            **info,
            'id': data.get('id'),
            'display_id': display_id,
            'title': data.get('title'),
            'language': data.get('language'),
            'thumbnails': thumbnails,
            'description': data.get('description'),
            'release_timestamp': data.get('earliest_start_date'),
            'series': data.get('series_title'),
            'season': data.get('season_title'),
            'season_number': data.get('season_no'),
            'season_id': data.get('season_id'),
            'episode': data.get('title'),
            'episode_number': data.get('episode_no'),
            'episode_id': data.get('id'),
        }