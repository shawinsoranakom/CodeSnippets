def _real_extract(self, url):
        path, episode_id = re.match(self._VALID_URL, url).groups()

        try:
            media = self._download_json(
                'https://videoservice.swm.digital/playback', episode_id, query={
                    'appId': '7plus',
                    'deviceType': 'web',
                    'platformType': 'web',
                    'accountId': 5303576322001,
                    'referenceId': 'ref:' + episode_id,
                    'deliveryId': 'csai',
                    'videoType': 'vod',
                })['media']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                raise ExtractorError(self._parse_json(
                    e.cause.read().decode(), episode_id)[0]['error_code'], expected=True)
            raise

        for source in media.get('sources', {}):
            src = source.get('src')
            if not src:
                continue
            source['src'] = update_url_query(src, {'rule': ''})

        info = self._parse_brightcove_metadata(media, episode_id)

        content = self._download_json(
            'https://component-cdn.swm.digital/content/' + path,
            episode_id, headers={
                'market-id': 4,
            }, fatal=False) or {}
        for item in content.get('items', {}):
            if item.get('componentData', {}).get('componentType') == 'infoPanel':
                for src_key, dst_key in [('title', 'title'), ('shortSynopsis', 'description')]:
                    value = item.get(src_key)
                    if value:
                        info[dst_key] = value
                info['series'] = try_get(
                    item, lambda x: x['seriesLogo']['name'], compat_str)
                mobj = re.search(r'^S(\d+)\s+E(\d+)\s+-\s+(.+)$', info['title'])
                if mobj:
                    info.update({
                        'season_number': int(mobj.group(1)),
                        'episode_number': int(mobj.group(2)),
                        'episode': mobj.group(3),
                    })

        return info