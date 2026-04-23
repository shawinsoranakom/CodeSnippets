def get_language_code_and_preference(fmt_stream):
            audio_track = fmt_stream.get('audioTrack') or {}
            display_name = audio_track.get('displayName') or ''
            language_code = audio_track.get('id', '').split('.')[0] or None
            if 'descriptive' in display_name.lower():
                return join_nonempty(language_code, 'desc'), -10
            if 'original' in display_name.lower():
                if language_code and not language_map.get(ORIGINAL_LANG_VALUE):
                    language_map[ORIGINAL_LANG_VALUE] = language_code
                return language_code, ORIGINAL_LANG_VALUE
            if audio_track.get('audioIsDefault'):
                if language_code and not language_map.get(DEFAULT_LANG_VALUE):
                    language_map[DEFAULT_LANG_VALUE] = language_code
                return language_code, DEFAULT_LANG_VALUE
            return language_code, -1