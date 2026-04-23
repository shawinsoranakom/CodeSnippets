def _real_extract(self, url):
        webpage = self._download_webpage(url, url)
        jsonld = self._search_json_ld(webpage, url)
        if not jsonld or 'url' not in jsonld:
            # try to extract from YouTube Player API
            # see https://developers.google.com/youtube/iframe_api_reference#Video_Queueing_Functions
            match_obj = re.search(r'\.cueVideoById\(\s*(?P<quote>[\'"])(?P<id>.*?)(?P=quote)', webpage)
            if match_obj:
                return self.url_result(match_obj.group('id'))
            # try to extract from twitter
            blockquote_el = get_element_by_attribute('class', 'twitter-tweet', webpage)
            if blockquote_el:
                matches = re.findall(
                    r'<a[^>]+href=\s*(?P<quote>[\'"])(?P<link>.*?)(?P=quote)',
                    blockquote_el)
                if matches:
                    for _, match in matches:
                        if '/status/' in match:
                            return self.url_result(match)
            raise ExtractorError('No video found!')
        if id not in jsonld:
            jsonld['id'] = url
        return jsonld