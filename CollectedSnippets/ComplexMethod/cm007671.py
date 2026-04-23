def _real_extract(self, url):
        show_path, episode_path = re.match(self._VALID_URL, url).groups()
        display_id = episode_path or show_path
        query = '''query {
  getShowBySlug(slug:"%s") {
    %%s
  }
}''' % show_path
        if episode_path:
            query = query % '''title
    getVideoBySlug(slug:"%s") {
      _id
      auth
      description
      duration
      episodeNumber
      launchDate
      mediaID
      seasonNumber
      poster
      title
      tvRating
    }''' % episode_path
            ['getVideoBySlug']
        else:
            query = query % '''metaDescription
    title
    videos(first:1000,sort:["episode_number"]) {
      edges {
        node {
           _id
           slug
        }
      }
    }'''
        show_data = self._download_json(
            'https://www.adultswim.com/api/search', display_id,
            data=json.dumps({'query': query}).encode(),
            headers={'Content-Type': 'application/json'})['data']['getShowBySlug']
        if episode_path:
            video_data = show_data['getVideoBySlug']
            video_id = video_data['_id']
            episode_title = title = video_data['title']
            series = show_data.get('title')
            if series:
                title = '%s - %s' % (series, title)
            info = {
                'id': video_id,
                'title': title,
                'description': strip_or_none(video_data.get('description')),
                'duration': float_or_none(video_data.get('duration')),
                'formats': [],
                'subtitles': {},
                'age_limit': parse_age_limit(video_data.get('tvRating')),
                'thumbnail': video_data.get('poster'),
                'timestamp': parse_iso8601(video_data.get('launchDate')),
                'series': series,
                'season_number': int_or_none(video_data.get('seasonNumber')),
                'episode': episode_title,
                'episode_number': int_or_none(video_data.get('episodeNumber')),
            }

            auth = video_data.get('auth')
            media_id = video_data.get('mediaID')
            if media_id:
                info.update(self._extract_ngtv_info(media_id, {
                    # CDN_TOKEN_APP_ID from:
                    # https://d2gg02c3xr550i.cloudfront.net/assets/asvp.e9c8bef24322d060ef87.bundle.js
                    'appId': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBJZCI6ImFzLXR2ZS1kZXNrdG9wLXB0enQ2bSIsInByb2R1Y3QiOiJ0dmUiLCJuZXR3b3JrIjoiYXMiLCJwbGF0Zm9ybSI6ImRlc2t0b3AiLCJpYXQiOjE1MzI3MDIyNzl9.BzSCk-WYOZ2GMCIaeVb8zWnzhlgnXuJTCu0jGp_VaZE',
                }, {
                    'url': url,
                    'site_name': 'AdultSwim',
                    'auth_required': auth,
                }))

            if not auth:
                extract_data = self._download_json(
                    'https://www.adultswim.com/api/shows/v1/videos/' + video_id,
                    video_id, query={'fields': 'stream'}, fatal=False) or {}
                assets = try_get(extract_data, lambda x: x['data']['video']['stream']['assets'], list) or []
                for asset in assets:
                    asset_url = asset.get('url')
                    if not asset_url:
                        continue
                    ext = determine_ext(asset_url, mimetype2ext(asset.get('mime_type')))
                    if ext == 'm3u8':
                        info['formats'].extend(self._extract_m3u8_formats(
                            asset_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
                    elif ext == 'f4m':
                        continue
                        # info['formats'].extend(self._extract_f4m_formats(
                        #     asset_url, video_id, f4m_id='hds', fatal=False))
                    elif ext in ('scc', 'ttml', 'vtt'):
                        info['subtitles'].setdefault('en', []).append({
                            'url': asset_url,
                        })
            self._sort_formats(info['formats'])

            return info
        else:
            entries = []
            for edge in show_data.get('videos', {}).get('edges', []):
                video = edge.get('node') or {}
                slug = video.get('slug')
                if not slug:
                    continue
                entries.append(self.url_result(
                    'http://adultswim.com/videos/%s/%s' % (show_path, slug),
                    'AdultSwim', video.get('_id')))
            return self.playlist_result(
                entries, show_path, show_data.get('title'),
                strip_or_none(show_data.get('metaDescription')))