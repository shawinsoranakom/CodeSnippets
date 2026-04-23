def process_manifest_format(f, proto, client_name, itag, missing_pot):
                key = (proto, f.get('language'))
                if not all_formats and key in itags[itag]:
                    return False

                # For handling potential pre-playback required waiting period
                if live_status not in ('is_live', 'post_live'):
                    f['available_at'] = available_at

                if f.get('source_preference') is None:
                    f['source_preference'] = -1

                # Deprioritize since its pre-merged m3u8 formats may have lower quality audio streams
                if client_name == 'web_safari' and proto == 'hls' and live_status != 'is_live':
                    f['source_preference'] -= 1

                if missing_pot:
                    f['format_note'] = join_nonempty(f.get('format_note'), 'MISSING POT', delim=' ')
                    f['source_preference'] -= 20

                itags[itag].add(key)

                if itag and all_formats:
                    f['format_id'] = f'{itag}-{proto}'
                elif any(p != proto for p, _ in itags[itag]):
                    f['format_id'] = f'{itag}-{proto}'
                elif itag:
                    f['format_id'] = itag

                lang_code = f.get('language')
                if lang_code and lang_code == language_map[ORIGINAL_LANG_VALUE]:
                    f['format_note'] = join_nonempty(f.get('format_note'), '(original)', delim=' ')
                    f['language_preference'] = ORIGINAL_LANG_VALUE
                elif lang_code and lang_code == language_map[DEFAULT_LANG_VALUE]:
                    f['format_note'] = join_nonempty(f.get('format_note'), '(default)', delim=' ')
                    f['language_preference'] = DEFAULT_LANG_VALUE

                if itag in ('616', '235'):
                    f['format_note'] = join_nonempty(f.get('format_note'), 'Premium', delim=' ')
                    f['source_preference'] += 100

                f['quality'] = q(itag_qualities.get(try_get(f, lambda f: f['format_id'].split('-')[0]), -1))
                if f['quality'] == -1 and f.get('height'):
                    f['quality'] = q(res_qualities[min(res_qualities, key=lambda x: abs(x - f['height']))])
                if self.get_param('verbose') or all_formats:
                    f['format_note'] = join_nonempty(
                        f.get('format_note'), short_client_name(client_name), delim=', ')
                if f.get('fps') and f['fps'] <= 1:
                    del f['fps']

                if proto == 'hls' and f.get('has_drm'):
                    f['has_drm'] = 'maybe'
                    f['source_preference'] -= 5
                return True