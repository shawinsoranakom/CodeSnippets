def _real_extract(self, url):
        gallery_id = self._match_id(url)

        data = self._call_api('albums', gallery_id, fatal=False, expected_status=404)

        info = traverse_obj(data, {
            'title': ('title', {lambda x: strip_or_none(x) or None}),
            'description': ('description', {self.get_description}),
        })

        if traverse_obj(data, 'is_album'):

            items = traverse_obj(data, (
                'media', lambda _, v: v.get('type') == 'video' or v['metadata']['is_animated'],
                'id', {lambda x: str_or_none(x) or None}))

            # if a gallery with exactly one video, apply album metadata to video
            media_id = None
            if self._GALLERY and len(items) == 1:
                media_id = items[0]

            if not media_id:
                result = self.playlist_result(
                    map(self._imgur_result, items), gallery_id)
                result.update(info)
                return result
            gallery_id = media_id

        result = self._imgur_result(gallery_id)
        info['_type'] = 'url_transparent'
        result.update(info)
        return result