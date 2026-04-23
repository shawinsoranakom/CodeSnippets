def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = dict_get(mobj.groupdict(), ('display_id', 'maus_id'), 'wdrmaus')
        webpage = self._download_webpage(url, display_id)

        entries = []

        # Article with several videos

        # for wdr.de the data-extension-ard is in a tag with the class "mediaLink"
        # for wdr.de radio players, in a tag with the class "wdrrPlayerPlayBtn"
        # for wdrmaus, in a tag with the class "videoButton" (previously a link
        # to the page in a multiline "videoLink"-tag)
        for mobj in re.finditer(
            r'''(?sx)class=
                    (?:
                        (["\'])(?:mediaLink|wdrrPlayerPlayBtn|videoButton)\b.*?\1[^>]+|
                        (["\'])videoLink\b.*?\2[\s]*>\n[^\n]*
                    )data-extension(?:-ard)?=(["\'])(?P<data>(?:(?!\3).)+)\3
                    ''', webpage):
            media_link_obj = self._parse_json(
                mobj.group('data'), display_id, transform_source=js_to_json,
                fatal=False)
            if not media_link_obj:
                continue
            jsonp_url = try_get(
                media_link_obj, lambda x: x['mediaObj']['url'], str)
            if jsonp_url:
                # metadata, or player JS with ['ref'] giving WDR id, or just media, perhaps
                clip_id = media_link_obj['mediaObj'].get('ref')
                if jsonp_url.endswith('.assetjsonp'):
                    asset = self._download_json(
                        jsonp_url, display_id, fatal=False, transform_source=strip_jsonp)
                    clip_id = try_get(asset, lambda x: x['trackerData']['trackerClipId'], str)
                if clip_id:
                    jsonp_url = self._asset_url(clip_id[4:])
                entries.append(self.url_result(jsonp_url, ie=WDRIE.ie_key()))

        # Playlist (e.g. https://www1.wdr.de/mediathek/video/sendungen/aktuelle-stunde/aktuelle-stunde-120.html)
        if not entries:
            entries = [
                self.url_result(
                    urllib.parse.urljoin(url, mobj.group('href')),
                    ie=WDRPageIE.ie_key())
                for mobj in re.finditer(
                    r'<a[^>]+\bhref=(["\'])(?P<href>(?:(?!\1).)+)\1[^>]+\bdata-extension(?:-ard)?=',
                    webpage) if re.match(self._PAGE_REGEX, mobj.group('href'))
            ]

        return self.playlist_result(entries, playlist_id=display_id)