def _real_extract(self, url):
        video_id = self._match_id(url)
        display_id = video_id.rstrip('@my')
        api_base = self._API_BASE_TMPL % video_id

        player_header = {
            'Referer': update_url_query(
                'http://tv.kakao.com/embed/player/cliplink/%s' % video_id, {
                    'service': 'kakao_tv',
                    'autoplay': '1',
                    'profile': 'HIGH',
                    'wmode': 'transparent',
                })
        }

        query = {
            'player': 'monet_html5',
            'referer': url,
            'uuid': '',
            'service': 'kakao_tv',
            'section': '',
            'dteType': 'PC',
            'fields': ','.join([
                '-*', 'tid', 'clipLink', 'displayTitle', 'clip', 'title',
                'description', 'channelId', 'createTime', 'duration', 'playCount',
                'likeCount', 'commentCount', 'tagList', 'channel', 'name', 'thumbnailUrl',
                'videoOutputList', 'width', 'height', 'kbps', 'profile', 'label'])
        }

        impress = self._download_json(
            api_base + 'impress', display_id, 'Downloading video info',
            query=query, headers=player_header)

        clip_link = impress['clipLink']
        clip = clip_link['clip']

        title = clip.get('title') or clip_link.get('displayTitle')

        query.update({
            'fields': '-*,code,message,url',
            'tid': impress.get('tid') or '',
        })

        formats = []
        for fmt in (clip.get('videoOutputList') or []):
            try:
                profile_name = fmt['profile']
                if profile_name == 'AUDIO':
                    continue
                query['profile'] = profile_name
                try:
                    fmt_url_json = self._download_json(
                        api_base + 'raw/videolocation', display_id,
                        'Downloading video URL for profile %s' % profile_name,
                        query=query, headers=player_header)
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        resp = self._parse_json(e.cause.read().decode(), video_id)
                        if resp.get('code') == 'GeoBlocked':
                            self.raise_geo_restricted()
                    continue

                fmt_url = fmt_url_json['url']
                formats.append({
                    'url': fmt_url,
                    'format_id': profile_name,
                    'width': int_or_none(fmt.get('width')),
                    'height': int_or_none(fmt.get('height')),
                    'format_note': fmt.get('label'),
                    'filesize': int_or_none(fmt.get('filesize')),
                    'tbr': int_or_none(fmt.get('kbps')),
                })
            except KeyError:
                pass
        self._sort_formats(formats)

        return {
            'id': display_id,
            'title': title,
            'description': strip_or_none(clip.get('description')),
            'uploader': try_get(clip_link, lambda x: x['channel']['name']),
            'uploader_id': str_or_none(clip_link.get('channelId')),
            'thumbnail': clip.get('thumbnailUrl'),
            'timestamp': unified_timestamp(clip_link.get('createTime')),
            'duration': int_or_none(clip.get('duration')),
            'view_count': int_or_none(clip.get('playCount')),
            'like_count': int_or_none(clip.get('likeCount')),
            'comment_count': int_or_none(clip.get('commentCount')),
            'formats': formats,
            'tags': clip.get('tagList'),
        }