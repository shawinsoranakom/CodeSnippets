def _extract_formats(self, info):
        formats = []
        song_id = info['id']
        for level in self._LEVELS:
            song = traverse_obj(
                self._call_player_api(song_id, level), ('data', lambda _, v: url_or_none(v['url']), any))
            if not song:
                break  # Media is not available due to removal or geo-restriction
            actual_level = song.get('level')
            if actual_level and actual_level != level:
                if level in ('lossless', 'jymaster'):
                    break  # We've already extracted the highest level of the user's account tier
                continue
            formats.append({
                'url': song['url'],
                'format_id': level,
                'vcodec': 'none',
                **traverse_obj(song, {
                    'ext': ('type', {str}),
                    'abr': ('br', {int_or_none(scale=1000)}),
                    'filesize': ('size', {int_or_none}),
                }),
            })
            if not actual_level:
                break  # Only 1 level is available if API does not return a value (netease:program)
        if not formats:
            self.raise_geo_restricted(
                'No media links found; possibly due to geo restriction', countries=['CN'])
        return formats