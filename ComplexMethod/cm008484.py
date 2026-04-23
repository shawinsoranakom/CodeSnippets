def _real_extract(self, url):
        scheme = 'https' if url.startswith('https') else 'http'

        audio_id = self._match_id(url)
        audio_info = self._download_json(
            f'{scheme}://m.ximalaya.com/tracks/{audio_id}.json', audio_id,
            'Downloading info json', 'Unable to download info file')

        formats = []
        # NOTE: VIP-restricted audio
        if audio_info.get('is_paid'):
            ts = int(time.time())
            vip_info = self._download_json(
                f'{scheme}://mpay.ximalaya.com/mobile/track/pay/{audio_id}/{ts}',
                audio_id, 'Downloading VIP info json', 'Unable to download VIP info file',
                query={'device': 'pc', 'isBackend': 'true', '_': ts})
            filename = self._decrypt_filename(vip_info['fileId'], vip_info['seed'])
            sign, token, timestamp = self._decrypt_url_params(vip_info['ep'])
            vip_url = update_url_query(
                f'{vip_info["domain"]}/download/{vip_info["apiVersion"]}{filename}', {
                    'sign': sign,
                    'token': token,
                    'timestamp': timestamp,
                    'buy_key': vip_info['buyKey'],
                    'duration': vip_info['duration'],
                })
            fmt = {
                'format_id': 'vip',
                'url': vip_url,
                'vcodec': 'none',
            }
            if '_preview_' in vip_url:
                self.report_warning(
                    f'This tracks requires a VIP account. Using a sample instead. {self._login_hint()}')
                fmt.update({
                    'format_note': 'Sample',
                    'preference': -10,
                    **traverse_obj(vip_info, {
                        'filesize': ('sampleLength', {int_or_none}),
                        'duration': ('sampleDuration', {int_or_none}),
                    }),
                })
            else:
                fmt.update(traverse_obj(vip_info, {
                    'filesize': ('totalLength', {int_or_none}),
                    'duration': ('duration', {int_or_none}),
                }))

            fmt['abr'] = try_call(lambda: fmt['filesize'] * 8 / fmt['duration'] / 1024)
            formats.append(fmt)

        formats.extend([{
            'format_id': f'{bps}k',
            'url': audio_info[k],
            'abr': bps,
            'vcodec': 'none',
        } for bps, k in ((24, 'play_path_32'), (64, 'play_path_64')) if audio_info.get(k)])

        thumbnails = []
        for k in audio_info:
            # cover pics kyes like: cover_url', 'cover_url_142'
            if k.startswith('cover_url'):
                thumbnail = {'name': k, 'url': audio_info[k]}
                if k == 'cover_url_142':
                    thumbnail['width'] = 180
                    thumbnail['height'] = 180
                thumbnails.append(thumbnail)

        audio_uploader_id = audio_info.get('uid')

        audio_description = try_call(
            lambda: audio_info['intro'].replace('\r\n\r\n\r\n ', '\n').replace('\r\n', '\n'))

        return {
            'id': audio_id,
            'uploader': audio_info.get('nickname'),
            'uploader_id': str_or_none(audio_uploader_id),
            'uploader_url': f'{scheme}://www.ximalaya.com/zhubo/{audio_uploader_id}/' if audio_uploader_id else None,
            'title': audio_info['title'],
            'thumbnails': thumbnails,
            'description': audio_description,
            'categories': list(filter(None, [audio_info.get('category_name')])),
            'duration': audio_info.get('duration'),
            'view_count': audio_info.get('play_count'),
            'like_count': audio_info.get('favorites_count'),
            'formats': formats,
        }