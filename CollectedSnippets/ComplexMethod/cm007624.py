def _extract_subtitles(url, video_data):
        STL_EXT = 'stl'
        SRT_EXT = 'srt'
        subtitles = {}
        subtitles_array = video_data.get('subtitlesArray') or []
        for k in ('subtitles', 'subtitlesUrl'):
            subtitles_array.append({'url': video_data.get(k)})
        for subtitle in subtitles_array:
            sub_url = subtitle.get('url')
            if sub_url and isinstance(sub_url, compat_str):
                sub_lang = subtitle.get('language') or 'it'
                sub_url = urljoin(url, sub_url)
                sub_ext = determine_ext(sub_url, SRT_EXT)
                subtitles.setdefault(sub_lang, []).append({
                    'ext': sub_ext,
                    'url': sub_url,
                })
                if STL_EXT == sub_ext:
                    subtitles[sub_lang].append({
                        'ext': SRT_EXT,
                        'url': sub_url[:-len(STL_EXT)] + SRT_EXT,
                    })
        return subtitles