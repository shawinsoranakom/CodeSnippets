def extract_formats(self, play_info):
        format_names = {
            r['quality']: traverse_obj(r, 'new_description', 'display_desc')
            for r in traverse_obj(play_info, ('support_formats', lambda _, v: v['quality']))
        }

        audios = traverse_obj(play_info, ('dash', (None, 'dolby'), 'audio', ..., {dict}))
        flac_audio = traverse_obj(play_info, ('dash', 'flac', 'audio'))
        if flac_audio:
            audios.append(flac_audio)
        formats = [{
            'url': traverse_obj(audio, 'baseUrl', 'base_url', 'url'),
            'ext': mimetype2ext(traverse_obj(audio, 'mimeType', 'mime_type')),
            'acodec': traverse_obj(audio, ('codecs', {str.lower})),
            'vcodec': 'none',
            'tbr': float_or_none(audio.get('bandwidth'), scale=1000),
            'filesize': int_or_none(audio.get('size')),
            'format_id': str_or_none(audio.get('id')),
        } for audio in audios]

        formats.extend({
            'url': traverse_obj(video, 'baseUrl', 'base_url', 'url'),
            'ext': mimetype2ext(traverse_obj(video, 'mimeType', 'mime_type')),
            'fps': float_or_none(traverse_obj(video, 'frameRate', 'frame_rate')),
            'width': int_or_none(video.get('width')),
            'height': int_or_none(video.get('height')),
            'vcodec': video.get('codecs'),
            'acodec': 'none' if audios else None,
            'dynamic_range': {126: 'DV', 125: 'HDR10'}.get(int_or_none(video.get('id'))),
            'tbr': float_or_none(video.get('bandwidth'), scale=1000),
            'filesize': int_or_none(video.get('size')),
            'quality': int_or_none(video.get('id')),
            'format_id': traverse_obj(
                video, (('baseUrl', 'base_url'), {self._FORMAT_ID_RE.search}, 1),
                ('id', {str_or_none}), get_all=False),
            'format': format_names.get(video.get('id')),
        } for video in traverse_obj(play_info, ('dash', 'video', ...)))

        if formats:
            self._check_missing_formats(play_info, formats)

        fragments = traverse_obj(play_info, ('durl', lambda _, v: url_or_none(v['url']), {
            'url': ('url', {url_or_none}),
            'duration': ('length', {float_or_none(scale=1000)}),
            'filesize': ('size', {int_or_none}),
        }))
        if fragments:
            formats.append({
                'url': fragments[0]['url'],
                'filesize': sum(traverse_obj(fragments, (..., 'filesize'))),
                **({
                    'fragments': fragments,
                    'protocol': 'http_dash_segments',
                } if len(fragments) > 1 else {}),
                **traverse_obj(play_info, {
                    'quality': ('quality', {int_or_none}),
                    'format_id': ('quality', {str_or_none}),
                    'format_note': ('quality', {format_names.get}),
                    'duration': ('timelength', {float_or_none(scale=1000)}),
                }),
                **parse_resolution(format_names.get(play_info.get('quality'))),
            })
        return formats