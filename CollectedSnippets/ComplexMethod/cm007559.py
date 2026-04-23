def _real_extract(self, url):
        video_id = self._match_id(url)

        clip = self._download_gql(
            video_id, [{
                'operationName': 'VideoAccessToken_Clip',
                'variables': {
                    'slug': video_id,
                },
            }],
            'Downloading clip access token GraphQL')[0]['data']['clip']

        if not clip:
            raise ExtractorError(
                'This clip is no longer available', expected=True)

        access_query = {
            'sig': clip['playbackAccessToken']['signature'],
            'token': clip['playbackAccessToken']['value'],
        }

        data = self._download_base_gql(
            video_id, {
                'query': '''{
  clip(slug: "%s") {
    broadcaster {
      displayName
    }
    createdAt
    curator {
      displayName
      id
    }
    durationSeconds
    id
    tiny: thumbnailURL(width: 86, height: 45)
    small: thumbnailURL(width: 260, height: 147)
    medium: thumbnailURL(width: 480, height: 272)
    title
    videoQualities {
      frameRate
      quality
      sourceURL
    }
    viewCount
  }
}''' % video_id}, 'Downloading clip GraphQL', fatal=False)

        if data:
            clip = try_get(data, lambda x: x['data']['clip'], dict) or clip

        formats = []
        for option in clip.get('videoQualities', []):
            if not isinstance(option, dict):
                continue
            source = url_or_none(option.get('sourceURL'))
            if not source:
                continue
            formats.append({
                'url': update_url_query(source, access_query),
                'format_id': option.get('quality'),
                'height': int_or_none(option.get('quality')),
                'fps': int_or_none(option.get('frameRate')),
            })
        self._sort_formats(formats)

        thumbnails = []
        for thumbnail_id in ('tiny', 'small', 'medium'):
            thumbnail_url = clip.get(thumbnail_id)
            if not thumbnail_url:
                continue
            thumb = {
                'id': thumbnail_id,
                'url': thumbnail_url,
            }
            mobj = re.search(r'-(\d+)x(\d+)\.', thumbnail_url)
            if mobj:
                thumb.update({
                    'height': int(mobj.group(2)),
                    'width': int(mobj.group(1)),
                })
            thumbnails.append(thumb)

        return {
            'id': clip.get('id') or video_id,
            'title': clip.get('title') or video_id,
            'formats': formats,
            'duration': int_or_none(clip.get('durationSeconds')),
            'views': int_or_none(clip.get('viewCount')),
            'timestamp': unified_timestamp(clip.get('createdAt')),
            'thumbnails': thumbnails,
            'creator': try_get(clip, lambda x: x['broadcaster']['displayName'], compat_str),
            'uploader': try_get(clip, lambda x: x['curator']['displayName'], compat_str),
            'uploader_id': try_get(clip, lambda x: x['curator']['id'], compat_str),
        }