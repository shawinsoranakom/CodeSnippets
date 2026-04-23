def _get_captions_by_type(self, video_id, subtitles_id, caption_type,
                              origin_lang_code=None):
        if not subtitles_id or not caption_type:
            return
        captions = {}
        for caption_entry in self._captions_xml.findall(
                self._CAPTIONS_ENTRY_TAG[caption_type]):
            caption_lang_code = caption_entry.attrib.get('lang_code')
            if not caption_lang_code:
                continue
            caption_format_data = []
            for caption_format in self._caption_formats_ext:
                query = {
                    'vid': subtitles_id,
                    'v': video_id,
                    'fmt': caption_format,
                    'lang': (caption_lang_code if origin_lang_code is None
                             else origin_lang_code),
                    'type': 'track',
                    'name': '',
                    'kind': '',
                }
                if origin_lang_code is not None:
                    query.update({'tlang': caption_lang_code})
                caption_format_data.append({
                    'url': update_url_query(self._BASE_URL_CAPTIONS, query),
                    'ext': caption_format,
                })
            captions[caption_lang_code] = caption_format_data
        return captions