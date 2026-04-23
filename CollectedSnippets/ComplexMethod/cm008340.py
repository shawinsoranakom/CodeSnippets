def _api_extract(self, video_id):
        meta = self._download_json(
            f'{self._BASE_API_URL}/video/{video_id}', video_id, headers=self._API_HEADERS)['video']

        uploader = traverse_obj(meta, ('author', 'login', {str}))

        formats = [{
            'url': quality['file'],
            'format': quality.get('title'),
            'resolution': quality.get('name'),
            'height': try_call(lambda: int(quality['name'][:-1])),
            'filesize': quality.get('length'),
        } for quality in meta['qualities'] if quality.get('file')]

        if meta.get('premium') and not meta.get('premium_free') and not formats:
            raise ExtractorError(
                'Video requires CDA Premium - subscription needed', expected=True)

        return {
            'id': video_id,
            'title': meta.get('title'),
            'description': meta.get('description'),
            'uploader': None if uploader == 'anonim' else uploader,
            'average_rating': float_or_none(meta.get('rating')),
            'thumbnail': meta.get('thumb'),
            'formats': formats,
            'duration': meta.get('duration'),
            'age_limit': 18 if meta.get('for_adults') else 0,
            'view_count': meta.get('views'),
        }