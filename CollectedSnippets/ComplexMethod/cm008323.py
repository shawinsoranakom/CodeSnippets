def _extract_storyboard(self, item_id, storyboard_json_url, duration):
        if not duration or not storyboard_json_url:
            return
        spec = self._download_json(storyboard_json_url, item_id, 'Downloading storyboard metadata JSON', fatal=False) or []
        # sort from highest quality to lowest
        # This makes sb0 the highest-quality format, sb1 - lower, etc which is consistent with youtube sb ordering
        spec.sort(key=lambda x: int_or_none(x.get('width')) or 0, reverse=True)
        base = base_url(storyboard_json_url)
        for i, s in enumerate(spec):
            count = int_or_none(s.get('count'))
            images = s.get('images')
            if not (images and count):
                continue
            fragment_duration = duration / len(images)
            yield {
                'format_id': f'sb{i}',
                'format_note': 'storyboard',
                'ext': 'mhtml',
                'protocol': 'mhtml',
                'acodec': 'none',
                'vcodec': 'none',
                'url': urljoin(base, images[0]),
                'width': int_or_none(s.get('width')),
                'height': int_or_none(s.get('height')),
                'fps': count / duration,
                'rows': int_or_none(s.get('rows')),
                'columns': int_or_none(s.get('cols')),
                'fragments': [{
                    'url': urljoin(base, path),
                    'duration': fragment_duration,
                } for path in images],
            }