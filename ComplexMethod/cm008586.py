def _real_extract(self, url):
        video_id = self._match_id(url)
        api_base = self._API_BASE_TMPL % video_id
        cdn_api_base = self._CDN_API % video_id

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
                'likeCount', 'commentCount', 'tagList', 'channel', 'name',
                'clipChapterThumbnailList', 'thumbnailUrl', 'timeInSec', 'isDefault',
                'videoOutputList', 'width', 'height', 'kbps', 'profile', 'label']),
        }

        api_json = self._download_json(
            api_base, video_id, 'Downloading video info')

        clip_link = api_json['clipLink']
        clip = clip_link['clip']

        title = clip.get('title') or clip_link.get('displayTitle')

        formats = []
        for fmt in clip.get('videoOutputList') or []:
            profile_name = fmt.get('profile')
            if not profile_name or profile_name == 'AUDIO':
                continue
            query.update({
                'profile': profile_name,
                'fields': '-*,code,message,url',
            })
            try:
                fmt_url_json = self._download_json(
                    cdn_api_base, video_id, query=query,
                    note=f'Downloading video URL for profile {profile_name}')
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                    resp = self._parse_json(e.cause.response.read().decode(), video_id)
                    if resp.get('code') == 'GeoBlocked':
                        self.raise_geo_restricted()
                raise

            fmt_url = traverse_obj(fmt_url_json, ('videoLocation', 'url'))
            if not fmt_url:
                continue

            formats.append({
                'url': fmt_url,
                'format_id': profile_name,
                'width': int_or_none(fmt.get('width')),
                'height': int_or_none(fmt.get('height')),
                'format_note': fmt.get('label'),
                'filesize': int_or_none(fmt.get('filesize')),
                'tbr': int_or_none(fmt.get('kbps')),
            })

        thumbs = []
        for thumb in clip.get('clipChapterThumbnailList') or []:
            thumbs.append({
                'url': thumb.get('thumbnailUrl'),
                'id': str(thumb.get('timeInSec')),
                'preference': -1 if thumb.get('isDefault') else 0,
            })
        top_thumbnail = clip.get('thumbnailUrl')
        if top_thumbnail:
            thumbs.append({
                'url': top_thumbnail,
                'preference': 10,
            })

        return {
            'id': video_id,
            'title': title,
            'description': strip_or_none(clip.get('description')),
            'uploader': traverse_obj(clip_link, ('channel', 'name')),
            'uploader_id': str_or_none(clip_link.get('channelId')),
            'thumbnails': thumbs,
            'timestamp': unified_timestamp(clip_link.get('createTime')),
            'duration': int_or_none(clip.get('duration')),
            'view_count': int_or_none(clip.get('playCount')),
            'like_count': int_or_none(clip.get('likeCount')),
            'comment_count': int_or_none(clip.get('commentCount')),
            'formats': formats,
            'tags': clip.get('tagList'),
        }