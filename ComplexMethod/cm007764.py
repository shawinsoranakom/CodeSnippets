def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'http://www.t-online.de/tv/id_%s/tid_json_video' % video_id, video_id)
        title = video_data['subtitle']

        formats = []
        for asset in video_data.get('assets', []):
            asset_source = asset.get('source') or asset.get('source2')
            if not asset_source:
                continue
            formats_id = []
            for field_key in ('type', 'profile'):
                field_value = asset.get(field_key)
                if field_value:
                    formats_id.append(field_value)
            formats.append({
                'format_id': '-'.join(formats_id),
                'url': asset_source,
            })

        thumbnails = []
        for image in video_data.get('images', []):
            image_source = image.get('source')
            if not image_source:
                continue
            thumbnails.append({
                'url': image_source,
            })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'thumbnails': thumbnails,
            'formats': formats,
        }