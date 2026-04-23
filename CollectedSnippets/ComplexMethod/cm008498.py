def _extract_vue_video(self, video_data, page_id=None):
        if isinstance(video_data, str):
            video_data = self._parse_json(video_data, page_id, transform_source=js_to_json)
        thumbnails = []
        image = video_data.get('image')
        if image:
            for thumb in (image if isinstance(image, list) else [image]):
                thmb_url = str_or_none(thumb.get('url'))
                if thmb_url:
                    thumbnails.append({
                        'url': thmb_url,
                    })
        is_website = video_data.get('type') == 'website'
        if is_website:
            url = video_data['url']
        else:
            url = 'tvp:' + str_or_none(video_data.get('_id') or page_id)
        return {
            '_type': 'url_transparent',
            'id': str_or_none(video_data.get('_id') or page_id),
            'url': url,
            'ie_key': (TVPIE if is_website else TVPEmbedIE).ie_key(),
            'title': str_or_none(video_data.get('title')),
            'description': str_or_none(video_data.get('lead')),
            'timestamp': int_or_none(video_data.get('release_date_long')),
            'duration': int_or_none(video_data.get('duration')),
            'thumbnails': thumbnails,
        }