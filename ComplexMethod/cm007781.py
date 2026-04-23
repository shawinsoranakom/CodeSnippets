def _get_video_info(self, itemdoc, use_hls=True):
        uri = itemdoc.find('guid').text
        video_id = self._id_from_uri(uri)
        self.report_extraction(video_id)
        content_el = itemdoc.find('%s/%s' % (_media_xml_tag('group'), _media_xml_tag('content')))
        mediagen_url = self._remove_template_parameter(content_el.attrib['url'])
        mediagen_url = mediagen_url.replace('device={device}', '')
        if 'acceptMethods' not in mediagen_url:
            mediagen_url += '&' if '?' in mediagen_url else '?'
            mediagen_url += 'acceptMethods='
            mediagen_url += 'hls' if use_hls else 'fms'

        mediagen_doc = self._download_xml(
            mediagen_url, video_id, 'Downloading video urls', fatal=False)

        if mediagen_doc is False:
            return None

        item = mediagen_doc.find('./video/item')
        if item is not None and item.get('type') == 'text':
            message = '%s returned error: ' % self.IE_NAME
            if item.get('code') is not None:
                message += '%s - ' % item.get('code')
            message += item.text
            raise ExtractorError(message, expected=True)

        description = strip_or_none(xpath_text(itemdoc, 'description'))

        timestamp = timeconvert(xpath_text(itemdoc, 'pubDate'))

        title_el = None
        if title_el is None:
            title_el = find_xpath_attr(
                itemdoc, './/{http://search.yahoo.com/mrss/}category',
                'scheme', 'urn:mtvn:video_title')
        if title_el is None:
            title_el = itemdoc.find(compat_xpath('.//{http://search.yahoo.com/mrss/}title'))
        if title_el is None:
            title_el = itemdoc.find(compat_xpath('.//title'))
            if title_el.text is None:
                title_el = None

        title = title_el.text
        if title is None:
            raise ExtractorError('Could not find video title')
        title = title.strip()

        # This a short id that's used in the webpage urls
        mtvn_id = None
        mtvn_id_node = find_xpath_attr(itemdoc, './/{http://search.yahoo.com/mrss/}category',
                                       'scheme', 'urn:mtvn:id')
        if mtvn_id_node is not None:
            mtvn_id = mtvn_id_node.text

        formats = self._extract_video_formats(mediagen_doc, mtvn_id, video_id)

        # Some parts of complete video may be missing (e.g. missing Act 3 in
        # http://www.southpark.de/alle-episoden/s14e01-sexual-healing)
        if not formats:
            return None

        self._sort_formats(formats)

        return {
            'title': title,
            'formats': formats,
            'subtitles': self._extract_subtitles(mediagen_doc, mtvn_id),
            'id': video_id,
            'thumbnail': self._get_thumbnail_url(uri, itemdoc),
            'description': description,
            'duration': float_or_none(content_el.attrib.get('duration')),
            'timestamp': timestamp,
        }