def _extract_embed(self, webpage, display_id, url):
        embed_url = (
            self._html_search_meta(
                'embedURL', webpage, 'embed URL',
                default=None)
            or self._search_regex(
                r'\bembedUrl["\']\s*:\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
                'embed URL', group='url', default=None)
            or self._search_regex(
                r'\bvar\s*sophoraID\s*=\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
                'embed URL', group='url', default=''))
        # some more work needed if we only found sophoraID
        if re.match(r'^[a-z]+\d+$', embed_url):
            # get the initial part of the url path,. eg /panorama/archiv/2022/
            parsed_url = compat_urllib_parse_urlparse(url)
            path = self._search_regex(r'(.+/)%s' % display_id, parsed_url.path or '', 'embed URL', default='')
            # find tell-tale image with the actual ID
            ndr_id = self._search_regex(r'%s([a-z]+\d+)(?!\.)\b' % (path, ), webpage, 'embed URL', default=None)
            # or try to use special knowledge!
            NDR_INFO_URL_TPL = 'https://www.ndr.de/info/%s-player.html'
            embed_url = 'ndr:%s' % (ndr_id, ) if ndr_id else NDR_INFO_URL_TPL % (embed_url, )
        if not embed_url:
            raise ExtractorError('Unable to extract embedUrl')

        description = self._search_regex(
            r'<p[^>]+itemprop="description">([^<]+)</p>',
            webpage, 'description', default=None) or self._og_search_description(webpage)
        timestamp = parse_iso8601(
            self._search_regex(
                (r'<span[^>]+itemprop="(?:datePublished|uploadDate)"[^>]+content="(?P<cont>[^"]+)"',
                 r'\bvar\s*pdt\s*=\s*(?P<q>["\'])(?P<cont>(?:(?!(?P=q)).)+)(?P=q)', ),
                webpage, 'upload date', group='cont', default=None))
        info = self._search_json_ld(webpage, display_id, default={})
        return merge_dicts({
            '_type': 'url_transparent',
            'url': embed_url,
            'display_id': display_id,
            'description': description,
            'timestamp': timestamp,
        }, info)