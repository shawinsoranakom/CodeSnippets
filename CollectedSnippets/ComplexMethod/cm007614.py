def _formats_key(f):
            # TODO remove the following workaround
            from ..utils import determine_ext
            if not f.get('ext') and 'url' in f:
                f['ext'] = determine_ext(f['url'])

            if isinstance(field_preference, (list, tuple)):
                return tuple(
                    f.get(field)
                    if f.get(field) is not None
                    else ('' if field == 'format_id' else -1)
                    for field in field_preference)

            preference = f.get('preference')
            if preference is None:
                preference = 0
                if f.get('ext') in ['f4f', 'f4m']:  # Not yet supported
                    preference -= 0.5

            protocol = f.get('protocol') or determine_protocol(f)
            proto_preference = 0 if protocol in ['http', 'https'] else (-0.5 if protocol == 'rtsp' else -0.1)

            if f.get('vcodec') == 'none':  # audio only
                preference -= 50
                if self.get_param('prefer_free_formats'):
                    ORDER = ['aac', 'mp3', 'm4a', 'webm', 'ogg', 'opus']
                else:
                    ORDER = ['webm', 'opus', 'ogg', 'mp3', 'aac', 'm4a']
                ext_preference = 0
                try:
                    audio_ext_preference = ORDER.index(f['ext'])
                except ValueError:
                    audio_ext_preference = -1
            else:
                if f.get('acodec') == 'none':  # video only
                    preference -= 40
                if self.get_param('prefer_free_formats'):
                    ORDER = ['flv', 'mp4', 'webm']
                else:
                    ORDER = ['webm', 'flv', 'mp4']
                try:
                    ext_preference = ORDER.index(f['ext'])
                except ValueError:
                    ext_preference = -1
                audio_ext_preference = 0

            return (
                preference,
                f.get('language_preference') if f.get('language_preference') is not None else -1,
                f.get('quality') if f.get('quality') is not None else -1,
                f.get('tbr') if f.get('tbr') is not None else -1,
                f.get('filesize') if f.get('filesize') is not None else -1,
                f.get('vbr') if f.get('vbr') is not None else -1,
                f.get('height') if f.get('height') is not None else -1,
                f.get('width') if f.get('width') is not None else -1,
                proto_preference,
                ext_preference,
                f.get('abr') if f.get('abr') is not None else -1,
                audio_ext_preference,
                f.get('fps') if f.get('fps') is not None else -1,
                f.get('filesize_approx') if f.get('filesize_approx') is not None else -1,
                f.get('source_preference') if f.get('source_preference') is not None else -1,
                f.get('format_id') if f.get('format_id') is not None else '',
            )