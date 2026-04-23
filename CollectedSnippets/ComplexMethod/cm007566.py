def _real_extract(self, url):
        video_id = self._match_id(url)

        player_page = self._download_json(
            'https://api.ardmediathek.de/public-gateway',
            video_id, data=json.dumps({
                'query': '''{
  playerPage(client: "ard", clipId: "%s") {
    blockedByFsk
    broadcastedOn
    maturityContentRating
    mediaCollection {
      _duration
      _geoblocked
      _isLive
      _mediaArray {
        _mediaStreamArray {
          _quality
          _server
          _stream
        }
      }
      _previewImage
      _subtitleUrl
      _type
    }
    show {
      title
    }
    synopsis
    title
    tracking {
      atiCustomVars {
        contentId
      }
    }
  }
}''' % video_id,
            }).encode(), headers={
                'Content-Type': 'application/json'
            })['data']['playerPage']
        title = player_page['title']
        content_id = str_or_none(try_get(
            player_page, lambda x: x['tracking']['atiCustomVars']['contentId']))
        media_collection = player_page.get('mediaCollection') or {}
        if not media_collection and content_id:
            media_collection = self._download_json(
                'https://www.ardmediathek.de/play/media/' + content_id,
                content_id, fatal=False) or {}
        info = self._parse_media_info(
            media_collection, content_id or video_id,
            player_page.get('blockedByFsk'))
        age_limit = None
        description = player_page.get('synopsis')
        maturity_content_rating = player_page.get('maturityContentRating')
        if maturity_content_rating:
            age_limit = int_or_none(maturity_content_rating.lstrip('FSK'))
        if not age_limit and description:
            age_limit = int_or_none(self._search_regex(
                r'\(FSK\s*(\d+)\)\s*$', description, 'age limit', default=None))
        info.update({
            'age_limit': age_limit,
            'title': title,
            'description': description,
            'timestamp': unified_timestamp(player_page.get('broadcastedOn')),
            'series': try_get(player_page, lambda x: x['show']['title']),
        })
        return info