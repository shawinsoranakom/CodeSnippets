def _real_extract(self, url):
        video_id = self._match_id(url)
        data_list = traverse_obj(self._download_json(
            'https://idolplus.com/api/zs/viewdata/ruleset/build', video_id,
            headers={'App_type': 'web', 'Country_Code': 'KR'}, query={
                'rulesetId': 'contents',
                'albumId': video_id,
                'distribute': 'PRD',
                'loggedIn': 'false',
                'region': 'zs',
                'countryGroup': '00010',
                'lang': 'en',
                'saId': '999999999998',
            }), ('data', 'viewData', ...))

        player_data = {}
        while data_list:
            player_data = data_list.pop()
            if traverse_obj(player_data, 'type') == 'player':
                break
            elif traverse_obj(player_data, ('dataList', ...)):
                data_list += player_data['dataList']

        formats = self._extract_m3u8_formats(traverse_obj(player_data, (
            'vodPlayerList', 'vodProfile', 0, 'vodServer', 0, 'video_url', {url_or_none})), video_id)

        subtitles = {}
        for caption in traverse_obj(player_data, ('vodPlayerList', 'caption')) or []:
            subtitles.setdefault(caption.get('lang') or 'und', []).append({
                'url': caption.get('smi_url'),
                'ext': 'vtt',
            })

        # Add member multicams as alternative formats
        if (traverse_obj(player_data, ('detail', 'has_cuesheet')) == 'Y'
                and traverse_obj(player_data, ('detail', 'is_omni_member')) == 'Y'):
            cuesheet = traverse_obj(self._download_json(
                'https://idolplus.com/gapi/contents/v1.0/content/cuesheet', video_id,
                'Downloading JSON metadata for member multicams',
                headers={'App_type': 'web', 'Country_Code': 'KR'}, query={
                    'ALBUM_ID': video_id,
                    'COUNTRY_GRP': '00010',
                    'LANG': 'en',
                    'SA_ID': '999999999998',
                    'COUNTRY_CODE': 'KR',
                }), ('data', 'cuesheet_item', 0))

            for member in traverse_obj(cuesheet, ('members', ...)):
                index = try_call(lambda: int(member['omni_view_index']) - 1)
                member_video_url = traverse_obj(cuesheet, ('omni_view', index, 'cdn_url', 0, 'url', {url_or_none}))
                if not member_video_url:
                    continue
                member_formats = self._extract_m3u8_formats(
                    member_video_url, video_id, note=f'Downloading m3u8 for multicam {member["name"]}')
                for mf in member_formats:
                    mf['format_id'] = f'{mf["format_id"]}-{member["name"].replace(" ", "_")}'
                formats.extend(member_formats)

        return {
            'id': video_id,
            'title': traverse_obj(player_data, ('detail', 'albumName')),
            'formats': formats,
            'subtitles': subtitles,
            'release_date': traverse_obj(player_data, ('detail', 'broadcastDate')),
        }