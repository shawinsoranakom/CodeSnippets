def _extract_video(self, video_id, url=None):
        info = self._download_json(
            f'https://www.alsace20.tv/visionneuse/visio_v9_js.php?key={video_id}&habillage=0&mode=html',
            video_id) or {}
        title = info.get('titre')

        formats = []
        for res, fmt_url in (info.get('files') or {}).items():
            formats.extend(
                self._extract_smil_formats(fmt_url, video_id, fatal=False)
                if '/smil:_' in fmt_url
                else self._extract_mpd_formats(fmt_url, video_id, mpd_id=res, fatal=False))

        webpage = (url and self._download_webpage(url, video_id, fatal=False)) or ''
        thumbnail = url_or_none(dict_get(info, ('image', 'preview')) or self._og_search_thumbnail(webpage))
        upload_date = self._search_regex(r'/(\d{6})_', thumbnail, 'upload_date', default=None)
        upload_date = unified_strdate(f'20{upload_date[:2]}-{upload_date[2:4]}-{upload_date[4:]}') if upload_date else None
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': clean_html(get_element_by_class('wysiwyg', webpage)),
            'upload_date': upload_date,
            'thumbnail': thumbnail,
            'duration': int_or_none(self._og_search_property('video:duration', webpage) if webpage else None),
            'view_count': int_or_none(info.get('nb_vues')),
        }