def extract_media(x_media_line):
            media = parse_m3u8_attributes(x_media_line)
            # As per [1, 4.3.4.1] TYPE, GROUP-ID and NAME are REQUIRED
            media_type, group_id, name = media.get('TYPE'), media.get('GROUP-ID'), media.get('NAME')
            if not (media_type and group_id and name):
                return
            groups.setdefault(group_id, []).append(media)
            if media_type not in ('VIDEO', 'AUDIO'):
                return
            media_url = media.get('URI')
            if media_url:
                format_id = []
                for v in (m3u8_id, group_id, name):
                    if v:
                        format_id.append(v)
                f = {
                    'format_id': '-'.join(format_id),
                    'url': format_url(media_url),
                    'manifest_url': m3u8_url,
                    'language': media.get('LANGUAGE'),
                    'ext': ext,
                    'protocol': entry_protocol,
                    'preference': preference,
                }
                if media_type == 'AUDIO':
                    f['vcodec'] = 'none'
                formats.append(f)