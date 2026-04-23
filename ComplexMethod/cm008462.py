def _get_subtitles(self, aweme_detail, aweme_id, user_name):
        # TODO: Extract text positioning info

        EXT_MAP = {  # From lowest to highest preference
            'creator_caption': 'json',
            'srt': 'srt',
            'webvtt': 'vtt',
        }
        preference = qualities(tuple(EXT_MAP.values()))

        subtitles = {}

        # aweme/detail endpoint subs
        captions_info = traverse_obj(
            aweme_detail, ('interaction_stickers', ..., 'auto_video_caption_info', 'auto_captions', ...), expected_type=dict)
        for caption in captions_info:
            caption_url = traverse_obj(caption, ('url', 'url_list', ...), expected_type=url_or_none, get_all=False)
            if not caption_url:
                continue
            caption_json = self._download_json(
                caption_url, aweme_id, note='Downloading captions', errnote='Unable to download captions', fatal=False)
            if not caption_json:
                continue
            subtitles.setdefault(caption.get('language', 'en'), []).append({
                'ext': 'srt',
                'data': '\n\n'.join(
                    f'{i + 1}\n{srt_subtitles_timecode(line["start_time"] / 1000)} --> {srt_subtitles_timecode(line["end_time"] / 1000)}\n{line["text"]}'
                    for i, line in enumerate(caption_json['utterances']) if line.get('text')),
            })
        # feed endpoint subs
        if not subtitles:
            for caption in traverse_obj(aweme_detail, ('video', 'cla_info', 'caption_infos', ...), expected_type=dict):
                if not caption.get('url'):
                    continue
                subtitles.setdefault(caption.get('lang') or 'en', []).append({
                    'url': caption['url'],
                    'ext': EXT_MAP.get(caption.get('Format')),
                })
        # webpage subs
        if not subtitles:
            if user_name:  # only _parse_aweme_video_app needs to extract the webpage here
                aweme_detail, _ = self._extract_web_data_and_status(
                    self._create_url(user_name, aweme_id), aweme_id, fatal=False)
            for caption in traverse_obj(aweme_detail, ('video', 'subtitleInfos', lambda _, v: v['Url'])):
                subtitles.setdefault(caption.get('LanguageCodeName') or 'en', []).append({
                    'url': caption['Url'],
                    'ext': EXT_MAP.get(caption.get('Format')),
                })

        # Deprioritize creator_caption json since it can't be embedded or used by media players
        for lang, subs_list in subtitles.items():
            subtitles[lang] = sorted(subs_list, key=lambda x: preference(x['ext']))

        return subtitles