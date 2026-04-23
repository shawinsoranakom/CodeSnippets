def _real_extract(self, url):
        video_id = self._match_id(url)

        metadata = self._download_json(
            f'https://app.veo.co/api/app/matches/{video_id}', video_id)

        video_data = self._download_json(
            f'https://app.veo.co/api/app/matches/{video_id}/videos', video_id, 'Downloading video data')

        formats = []
        for fmt in video_data:
            mimetype = str_or_none(fmt.get('mime_type'))
            format_url = url_or_none(fmt.get('url'))
            # skip configuration file for panoramic video
            if not format_url or mimetype == 'video/mp2t':
                continue

            height = int_or_none(fmt.get('height'))
            render_type = str_or_none(fmt.get('render_type'))
            format_id = f'{render_type}-{height}p' if render_type and height else None

            # Veo returns panoramic video information even if panoramic video is not available.
            # e.g. https://app.veo.co/matches/20201027-last-period/
            if render_type == 'panorama':
                if not self._is_valid_url(format_url, video_id, format_id):
                    continue

            formats.append({
                'url': format_url,
                'format_id': format_id,
                'ext': mimetype2ext(mimetype),
                'width': int_or_none(fmt.get('width')),
                'height': height,
                'vbr': int_or_none(fmt.get('bit_rate'), scale=1000),
            })

        return {
            'id': video_id,
            'title': str_or_none(metadata.get('title')),
            'formats': formats,
            'thumbnail': url_or_none(metadata.get('thumbnail')),
            'timestamp': unified_timestamp(metadata.get('created')),
            'view_count': int_or_none(metadata.get('view_count')),
            'duration': int_or_none(metadata.get('duration')),
        }