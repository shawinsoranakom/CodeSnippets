def _real_extract(self, url):
        video_id = self._match_id(url).upper()

        token = self._download_json(
            'https://auth.redbullmediahouse.com/token', video_id,
            'Downloading token', data=urlencode_postdata({
                'grant_type': 'client_credentials',
            }), headers={
                'Authorization': 'Basic SVgtMjJYNEhBNFdEM1cxMTpEdDRVSkFLd2ZOMG5IMjB1NGFBWTBmUFpDNlpoQ1EzNA==',
            })
        access_token = token['access_token']
        token_type = token.get('token_type', 'Bearer')

        video = self._download_json(
            'https://sparkle-api.liiift.io/api/v1/stv/channels/international/assets/%s' % video_id,
            video_id, 'Downloading video JSON', headers={
                'Authorization': '%s %s' % (token_type, access_token),
            })

        formats = []
        thumbnail = None
        for resource in video['resources']:
            if not isinstance(resource, dict):
                continue
            format_url = url_or_none(resource.get('url'))
            if not format_url:
                continue
            extension = resource.get('extension')
            type_ = resource.get('type')
            if extension == 'jpg' or type_ == 'reference_keyframe':
                thumbnail = format_url
                continue
            ext = determine_ext(format_url)
            if type_ == 'dash' or ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id='dash', fatal=False))
            elif type_ == 'hls' or ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif extension == 'mp4' or ext == 'mp4':
                formats.append({
                    'url': format_url,
                    'format_id': type_,
                    'width': int_or_none(resource.get('width')),
                    'height': int_or_none(resource.get('height')),
                })
        self._sort_formats(formats)

        attrs = {}
        for attribute in video['attributes']:
            if not isinstance(attribute, dict):
                continue
            key = attribute.get('fieldKey')
            value = attribute.get('fieldValue')
            if not key or not value:
                continue
            attrs[key] = value

        title = attrs.get('title_stv') or video_id
        alt_title = attrs.get('title')
        description = attrs.get('long_description') or attrs.get('short_description')
        series = attrs.get('label')
        season = attrs.get('season')
        episode = attrs.get('chapter')
        duration = float_or_none(attrs.get('duration'), scale=1000)
        season_number = int_or_none(self._search_regex(
            r'Season (\d+)', season or '', 'season number', default=None))
        episode_number = int_or_none(self._search_regex(
            r'Episode (\d+)', episode or '', 'episode number', default=None))

        return {
            'id': video_id,
            'title': title,
            'alt_title': alt_title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': unified_timestamp(video.get('lastPublished')),
            'series': series,
            'season': season,
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
            'formats': formats,
        }