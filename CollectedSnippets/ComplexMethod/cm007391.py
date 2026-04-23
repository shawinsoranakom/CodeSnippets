def _extract_mobile(self, video_id):
        video = self._download_json(
            'https://zdf-cdn.live.cellular.de/mediathekV2/document/%s' % video_id,
            video_id)

        formats = []
        formitaeten = try_get(video, lambda x: x['document']['formitaeten'], list)
        document = formitaeten and video['document']
        if formitaeten:
            title = document['titel']
            content_id = document['basename']

            format_urls = set()
            for f in formitaeten or []:
                self._extract_format(content_id, formats, format_urls, f)
        self._sort_formats(formats)

        thumbnails = []
        teaser_bild = document.get('teaserBild')
        if isinstance(teaser_bild, dict):
            for thumbnail_key, thumbnail in teaser_bild.items():
                thumbnail_url = try_get(
                    thumbnail, lambda x: x['url'], compat_str)
                if thumbnail_url:
                    thumbnails.append({
                        'url': thumbnail_url,
                        'id': thumbnail_key,
                        'width': int_or_none(thumbnail.get('width')),
                        'height': int_or_none(thumbnail.get('height')),
                    })

        return {
            'id': content_id,
            'title': title,
            'description': document.get('beschreibung'),
            'duration': int_or_none(document.get('length')),
            'timestamp': unified_timestamp(document.get('date')) or unified_timestamp(
                try_get(video, lambda x: x['meta']['editorialDate'], compat_str)),
            'thumbnails': thumbnails,
            'subtitles': self._extract_subtitles(document),
            'formats': formats,
        }