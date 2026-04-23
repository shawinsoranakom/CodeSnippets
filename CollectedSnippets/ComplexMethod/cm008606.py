def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, impersonate=True)

        props_list = traverse_obj(webpage, (
            {self._ASTRO_ISLAND_RE.findall}, ...,
            {extract_attributes}, 'props', {json.loads}))

        description = traverse_obj(props_list, (..., 'leadParagraph', 1, {clean_html}, any, filter))
        main_content = traverse_obj(props_list, (..., ('content', ('articleData', 1, 'opening')), 1, {dict}, any))

        if traverse_obj(props_list, (..., 'editorialType', 1, {str}, any)) != 'VID':  # e.g. 'ART'
            entries = []

            for p in traverse_obj(props_list, (..., 'articleData', 1, ('opening', ('body', 1, ...)), 1, {dict})):
                type_ = traverse_obj(p, ('type', 1, {str}))
                content = traverse_obj(p, ('content', 1, {str} if type_ == 'paragraph' else {dict}))
                if not content:
                    continue
                if type_ == 'paragraph':
                    description = join_nonempty(description, content, delim='')
                elif type_ == 'video':
                    entries.append(self._parse_content(content, url))
                else:
                    self.report_warning(
                        f'Skipping unsupported content type "{type_}"', display_id, only_once=True)

            return self.playlist_result(
                entries,
                traverse_obj(props_list, (..., 'id', 1, {int}, {str_or_none}, any)) or display_id,
                traverse_obj(main_content, ('dataTitle', 1, {str})),
                clean_html(description))

        if not main_content:
            raise ExtractorError('Unable to extract main content from webpage')

        info = self._parse_content(main_content, url)
        info['description'] = description

        return info