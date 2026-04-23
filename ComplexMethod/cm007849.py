def process_manifest_format(f, proto, client_name, itag, all_formats=False):
            key = (proto, f.get('language'))
            if not all_formats and key in itags[itag]:
                return False
            itags[itag].add(key)

            if itag:
                f['format_id'] = (
                    '{0}-{1}'.format(itag, proto)
                    if all_formats or any(p != proto for p, _ in itags[itag])
                    else itag)

            if f.get('source_preference') is None:
                f['source_preference'] = -1

            # Deprioritize since its pre-merged m3u8 formats may have lower quality audio streams
            if client_name == 'web_safari' and proto == 'hls' and not is_live:
                f['source_preference'] -= 1

            if itag in ('616', '235'):
                f['format_note'] = join_nonempty(f.get('format_note'), 'Premium', delim=' ')
                f['source_preference'] += 100

            f['quality'] = q(traverse_obj(f, (
                'format_id', T(lambda s: itag_qualities[s.split('-')[0]])), default=-1))
            if try_call(lambda: f['fps'] <= 1):
                del f['fps']

            if proto == 'hls' and f.get('has_drm'):
                f['has_drm'] = 'maybe'
                f['source_preference'] -= 5
            return True