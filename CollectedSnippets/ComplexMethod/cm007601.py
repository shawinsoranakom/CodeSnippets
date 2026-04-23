def _parse_smil(self, smil, smil_url, video_id, f4m_params=None):
        namespace = self._parse_smil_namespace(smil)

        formats = self._parse_smil_formats(
            smil, smil_url, video_id, namespace=namespace, f4m_params=f4m_params)
        subtitles = self._parse_smil_subtitles(smil, namespace=namespace)

        video_id = os.path.splitext(url_basename(smil_url))[0]
        title = None
        description = None
        upload_date = None
        for meta in smil.findall(self._xpath_ns('./head/meta', namespace)):
            name = meta.attrib.get('name')
            content = meta.attrib.get('content')
            if not name or not content:
                continue
            if not title and name == 'title':
                title = content
            elif not description and name in ('description', 'abstract'):
                description = content
            elif not upload_date and name == 'date':
                upload_date = unified_strdate(content)

        thumbnails = [{
            'id': image.get('type'),
            'url': image.get('src'),
            'width': int_or_none(image.get('width')),
            'height': int_or_none(image.get('height')),
        } for image in smil.findall(self._xpath_ns('.//image', namespace)) if image.get('src')]

        return {
            'id': video_id,
            'title': title or video_id,
            'description': description,
            'upload_date': upload_date,
            'thumbnails': thumbnails,
            'formats': formats,
            'subtitles': subtitles,
        }