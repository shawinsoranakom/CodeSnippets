def _real_extract(self, url):
        video_id, name = self._match_valid_url(url).groups()
        display_id = name or video_id

        webpage_url = 'http://www.gdcvault.com/play/' + video_id
        start_page = self._download_webpage(webpage_url, display_id)

        direct_url = self._search_regex(
            r's1\.addVariable\("file",\s*encodeURIComponent\("(/[^"]+)"\)\);',
            start_page, 'url', default=None)
        if direct_url:
            title = self._html_search_regex(
                r'<td><strong>Session Name:?</strong></td>\s*<td>(.*?)</td>',
                start_page, 'title')
            video_url = 'http://www.gdcvault.com' + direct_url
            # resolve the url so that we can detect the correct extension
            video_url = self._request_webpage(
                HEADRequest(video_url), video_id).url

            return {
                'id': video_id,
                'display_id': display_id,
                'url': video_url,
                'title': title,
            }

        embed_url = KalturaIE._extract_url(start_page)
        if embed_url:
            embed_url = smuggle_url(embed_url, {'source_url': url})
            ie_key = 'Kaltura'
        else:
            PLAYER_REGEX = r'<iframe src="(?P<xml_root>.+?)/(?:gdc-)?player.*?\.html.*?".*?</iframe>'

            xml_root = self._html_search_regex(
                PLAYER_REGEX, start_page, 'xml root', default=None)
            if xml_root is None:
                # Probably need to authenticate
                login_res = self._login(webpage_url, display_id)
                if login_res is None:
                    self.report_warning('Could not login.')
                else:
                    start_page = login_res
                    # Grab the url from the authenticated page
                    xml_root = self._html_search_regex(
                        PLAYER_REGEX, start_page, 'xml root')

            xml_name = self._html_search_regex(
                r'<iframe src=".*?\?xml(?:=|URL=xml/)(.+?\.xml).*?".*?</iframe>',
                start_page, 'xml filename', default=None)
            if not xml_name:
                info = self._parse_html5_media_entries(url, start_page, video_id)[0]
                info.update({
                    'title': remove_start(self._search_regex(
                        r'>Session Name:\s*<.*?>\s*<td>(.+?)</td>', start_page,
                        'title', default=None) or self._og_search_title(
                        start_page, default=None), 'GDC Vault - '),
                    'id': video_id,
                    'display_id': display_id,
                })
                return info
            embed_url = f'{xml_root}/xml/{xml_name}'
            ie_key = 'DigitallySpeaking'

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'display_id': display_id,
            'url': embed_url,
            'ie_key': ie_key,
        }