def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        domain_id = mobj.group('domain_id') or mobj.group('domain_id_s')
        video_id = mobj.group('id')

        video = None

        def find_video(result):
            if isinstance(result, dict):
                return result
            elif isinstance(result, list):
                vid = int(video_id)
                for v in result:
                    if try_get(v, lambda x: x['general']['ID'], int) == vid:
                        return v
            return None

        response = self._download_json(
            f'https://arc.nexx.cloud/api/video/{video_id}.json',
            video_id, fatal=False)
        if response and isinstance(response, dict):
            result = response.get('result')
            if result:
                video = find_video(result)

        # not all videos work via arc, e.g. nexx:741:1269984
        if not video:
            # Reverse engineered from JS code (see getDeviceID function)
            device_id = f'{random.randint(1, 4)}:{int(time.time())}:{random.randint(10000, 99999)}{random.randint(1, 9)}'

            result = self._call_api(domain_id, 'session/init', video_id, data={
                'nxp_devh': device_id,
                'nxp_userh': '',
                'precid': '0',
                'playlicense': '0',
                'screenx': '1920',
                'screeny': '1080',
                'playerversion': '6.0.00',
                'gateway': 'html5',
                'adGateway': '',
                'explicitlanguage': 'en-US',
                'addTextTemplates': '1',
                'addDomainData': '1',
                'addAdModel': '1',
            }, headers={
                'X-Request-Enable-Auth-Fallback': '1',
            })

            cid = result['general']['cid']

            # As described in [1] X-Request-Token generation algorithm is
            # as follows:
            #   md5( operation + domain_id + domain_secret )
            # where domain_secret is a static value that will be given by nexx.tv
            # as per [1]. Here is how this "secret" is generated (reversed
            # from _play._factory.data.getDomainData function, search for
            # domaintoken or enableAPIAccess). So it's actually not static
            # and not that much of a secret.
            # 1. https://nexxtvstorage.blob.core.windows.net/files/201610/27.pdf
            secret = result['device']['domaintoken'][int(device_id[0]):]
            secret = secret[0:len(secret) - int(device_id[-1])]

            op = 'byid'

            # Reversed from JS code for _play.api.call function (search for
            # X-Request-Token)
            request_token = hashlib.md5(
                ''.join((op, domain_id, secret)).encode()).hexdigest()

            result = self._call_api(
                domain_id, f'videos/{op}/{video_id}', video_id, data={
                    'additionalfields': 'language,channel,format,licenseby,slug,fileversion,episode,season',
                    'addInteractionOptions': '1',
                    'addStatusDetails': '1',
                    'addStreamDetails': '1',
                    'addFeatures': '1',
                    # Caption format selection doesn't seem to be enforced?
                    'addCaptions': 'vtt',
                    'addScenes': '1',
                    'addChapters': '1',
                    'addHotSpots': '1',
                    'addConnectedMedia': 'persons',
                    'addBumpers': '1',
                }, headers={
                    'X-Request-CID': cid,
                    'X-Request-Token': request_token,
                })
            video = find_video(result)

        general = video['general']
        title = general['title']

        cdn = video['streamdata']['cdnType']

        if cdn == 'azure':
            formats = self._extract_azure_formats(video, video_id)
        elif cdn == 'free':
            formats = self._extract_free_formats(video, video_id)
        elif cdn == '3q':
            formats = self._extract_3q_formats(video, video_id)
        else:
            self.raise_no_formats(f'{cdn} formats are currently not supported', video_id)

        subtitles = {}
        for sub in video.get('captiondata') or []:
            if sub.get('data'):
                subtitles.setdefault(sub.get('language', 'en'), []).append({
                    'ext': 'srt',
                    'data': '\n\n'.join(
                        f'{i + 1}\n{srt_subtitles_timecode(line["fromms"] / 1000)} --> {srt_subtitles_timecode(line["toms"] / 1000)}\n{line["caption"]}'
                        for i, line in enumerate(sub['data'])),
                    'name': sub.get('language_long') or sub.get('title'),
                })
            elif sub.get('url'):
                subtitles.setdefault(sub.get('language', 'en'), []).append({
                    'url': sub['url'],
                    'ext': sub.get('format'),
                    'name': sub.get('language_long') or sub.get('title'),
                })

        return {
            'id': video_id,
            'title': title,
            'alt_title': general.get('subtitle'),
            'description': general.get('description'),
            'release_year': int_or_none(general.get('year')),
            'creator': general.get('studio') or general.get('studio_adref') or None,
            'thumbnail': try_get(
                video, lambda x: x['imagedata']['thumb'], str),
            'duration': parse_duration(general.get('runtime')),
            'timestamp': int_or_none(general.get('uploaded')),
            'episode_number': traverse_obj(
                video, (('episodedata', 'general'), 'episode'), expected_type=int, get_all=False),
            'season_number': traverse_obj(
                video, (('episodedata', 'general'), 'season'), expected_type=int, get_all=False),
            'cast': traverse_obj(video, ('connectedmedia', ..., 'title'), expected_type=str),
            'formats': formats,
            'subtitles': subtitles,
        }