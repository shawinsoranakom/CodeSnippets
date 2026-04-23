def _extract_from_webpage(self, url, webpage):
        # Common function for the WordPress plugin version only.
        mb_player_params = self._search_regex(
            r'function\s*initializeMiniAudioPlayer\(\){[^}]+jQuery([^;]+)\.mb_miniPlayer',
            webpage, 'mb player params', default=None)
        if not mb_player_params:
            return
        # v1.55 - 1.9.3 has "a[href*='.mp3'] ,a[href*='.m4a']"
        # v1.9.4+ has "a[href*='.mp3']" only
        file_exts = re.findall(r'a\[href\s*\*=\s*\'\.([a-zA-Z\d]+)\'', mb_player_params)
        if not file_exts:
            return

        candidates = get_elements_text_and_html_by_attribute(
            'href', rf'(?:[^\"\']+\.(?:{"|".join(file_exts)}))', webpage, escape_value=False, tag='a')

        for title, html in candidates:
            attrs = extract_attributes(html)
            # XXX: not tested - have not found any example of it being used
            if any(c in (attrs.get('class') or '') for c in re.findall(r'\.not\("\.([^"]+)', mb_player_params)):
                continue
            href = attrs['href']
            yield {
                'id': self._generic_id(href),
                'title': title or self._generic_title(href),
                'url': href,
            }