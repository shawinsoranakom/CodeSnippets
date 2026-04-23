def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = self._match_valid_url(url)
        partner_id, entry_id, player_type = mobj.group('partner_id', 'id', 'player_type')
        ks, captions = None, None
        if not player_type:
            player_type = 'kwidget' if 'html5lib/v2' in url else 'html5'
        if partner_id and entry_id:
            _, info, flavor_assets, captions = self._get_video_info(entry_id, partner_id, smuggled_data.get('service_url'), player_type=player_type)
        else:
            path, query = mobj.group('path', 'query')
            if not path and not query:
                raise ExtractorError('Invalid URL', expected=True)
            params = {}
            if query:
                params = urllib.parse.parse_qs(query)
            if path:
                splitted_path = path.split('/')
                params.update(dict(zip(splitted_path[::2], [[v] for v in splitted_path[1::2]])))  # noqa: B905
            if 'wid' in params:
                partner_id = remove_start(params['wid'][0], '_')
            elif 'p' in params:
                partner_id = params['p'][0]
            elif 'partner_id' in params:
                partner_id = params['partner_id'][0]
            else:
                raise ExtractorError('Invalid URL', expected=True)
            if 'entry_id' in params:
                entry_id = params['entry_id'][0]
                _, info, flavor_assets, captions = self._get_video_info(entry_id, partner_id, player_type=player_type)
            elif 'uiconf_id' in params and 'flashvars[referenceId]' in params:
                reference_id = params['flashvars[referenceId]'][0]
                webpage = self._download_webpage(url, reference_id)
                entry_data = self._search_json(
                    self.IFRAME_PACKAGE_DATA_REGEX, webpage,
                    'kalturaIframePackageData', reference_id)['entryResult']
                info, flavor_assets = entry_data['meta'], entry_data['contextData']['flavorAssets']
                entry_id = info['id']
                # Unfortunately, data returned in kalturaIframePackageData lacks
                # captions so we will try requesting the complete data using
                # regular approach since we now know the entry_id
                # Even if this fails we already have everything extracted
                # apart from captions and can process at least with this
                with contextlib.suppress(ExtractorError):
                    _, info, flavor_assets, captions = self._get_video_info(
                        entry_id, partner_id, player_type=player_type)
            elif 'uiconf_id' in params and 'flashvars[playlistAPI.kpl0Id]' in params:
                playlist_id = params['flashvars[playlistAPI.kpl0Id]'][0]
                webpage = self._download_webpage(url, playlist_id)
                playlist_data = self._search_json(
                    self.IFRAME_PACKAGE_DATA_REGEX, webpage,
                    'kalturaIframePackageData', playlist_id)['playlistResult']
                return self.playlist_from_matches(
                    traverse_obj(playlist_data, (playlist_id, 'items', ..., 'id')),
                    playlist_id, traverse_obj(playlist_data, (playlist_id, 'name')),
                    ie=KalturaIE, getter=lambda x: f'kaltura:{partner_id}:{x}:{player_type}')
            else:
                raise ExtractorError('Invalid URL', expected=True)
            ks = params.get('flashvars[ks]', [None])[0]

        return self._per_video_extract(smuggled_data, entry_id, info, ks, flavor_assets, captions)