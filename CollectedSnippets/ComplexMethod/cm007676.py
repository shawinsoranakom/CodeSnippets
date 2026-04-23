def _real_extract(self, url):
        display_id = self._match_id(url)

        response = self._graphql_call('''{
  %%s(slug: "%%s") {
    ... on RecordSlug {
      record {
        %s
      }
    }
    ... on PageSlug {
      child {
        id
      }
    }
    ... on NotFoundSlug {
      status
    }
  }
}''' % self._RECORD_TEMPL, 'Slug', display_id)
        if response.get('status'):
            raise ExtractorError('This video is no longer available.', expected=True)

        child = response.get('child')
        if child:
            record = self._graphql_call('''{
  %%s(id: "%%s") {
    ... on Video {
      %s
    }
  }
}''' % self._RECORD_TEMPL, 'Record', child['id'])
        else:
            record = response['record']
        video_id = record['id']

        info = {
            'id': video_id,
            'display_id': display_id,
            'title': record['title'],
            'thumbnail': record.get('thumb', {}).get('preview'),
            'description': record.get('teaser'),
            'duration': parse_duration(record.get('duration')),
            'timestamp': parse_iso8601(record.get('publishOn')),
        }

        media_id = record.get('turnerMediaId')
        if media_id:
            self._initialize_geo_bypass({
                'countries': ['US'],
            })
            info.update(self._extract_ngtv_info(media_id, {
                'accessToken': record['turnerMediaAuthToken'],
                'accessTokenType': 'jws',
            }))
        else:
            video_sources = self._download_json(
                'https://teamcoco.com/_truman/d/' + video_id,
                video_id)['meta']['src']
            if isinstance(video_sources, dict):
                video_sources = video_sources.values()

            formats = []
            get_quality = qualities(['low', 'sd', 'hd', 'uhd'])
            for src in video_sources:
                if not isinstance(src, dict):
                    continue
                src_url = src.get('src')
                if not src_url:
                    continue
                format_id = src.get('label')
                ext = determine_ext(src_url, mimetype2ext(src.get('type')))
                if format_id == 'hls' or ext == 'm3u8':
                    # compat_urllib_parse.urljoin does not work here
                    if src_url.startswith('/'):
                        src_url = 'http://ht.cdn.turner.com/tbs/big/teamcoco' + src_url
                    formats.extend(self._extract_m3u8_formats(
                        src_url, video_id, 'mp4', m3u8_id=format_id, fatal=False))
                else:
                    if src_url.startswith('/mp4:protected/'):
                        # TODO Correct extraction for these files
                        continue
                    tbr = int_or_none(self._search_regex(
                        r'(\d+)k\.mp4', src_url, 'tbr', default=None))

                    formats.append({
                        'url': src_url,
                        'ext': ext,
                        'tbr': tbr,
                        'format_id': format_id,
                        'quality': get_quality(format_id),
                    })
            self._sort_formats(formats)
            info['formats'] = formats

        return info