def _real_extract(self, url):
        post_id = self._match_id(url)

        webpage = self._download_payload('wkview', post_id, {
            'act': 'show',
            'w': 'wall' + post_id,
        })[1]

        description = clean_html(get_element_by_class('wall_post_text', webpage))
        uploader = clean_html(get_element_by_class('author', webpage))

        entries = []

        for audio in re.findall(r'data-audio="([^"]+)', webpage):
            audio = self._parse_json(unescapeHTML(audio), post_id)
            a = self._AUDIO._make(audio[:16])
            if not a.url:
                continue
            title = unescapeHTML(a.title)
            performer = unescapeHTML(a.performer)
            entries.append({
                'id': '%s_%s' % (a.owner_id, a.id),
                'url': self._unmask_url(a.url, a.ads['vk_id']),
                'title': '%s - %s' % (performer, title) if performer else title,
                'thumbnails': [{'url': c_url} for c_url in a.cover_url.split(',')] if a.cover_url else None,
                'duration': int_or_none(a.duration),
                'uploader': uploader,
                'artist': performer,
                'track': title,
                'ext': 'mp4',
                'protocol': 'm3u8',
            })

        for video in re.finditer(
                r'<a[^>]+href=(["\'])(?P<url>/video(?:-?[\d_]+).*?)\1', webpage):
            entries.append(self.url_result(
                compat_urlparse.urljoin(url, video.group('url')), VKIE.ie_key()))

        title = 'Wall post %s' % post_id

        return self.playlist_result(
            orderedSet(entries), post_id,
            '%s - %s' % (uploader, title) if uploader else title,
            description)