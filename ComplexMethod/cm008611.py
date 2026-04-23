def _get_live_status_and_session_id(self, content_code, data_json):
        video_type = data_json.get('type')
        live_finished_at = data_json.get('live_finished_at')

        payload = {}
        if video_type == 'vod':
            if live_finished_at:
                live_status = 'was_live'
            else:
                live_status = 'not_live'
        elif video_type == 'live':
            if not data_json.get('live_started_at'):
                return 'is_upcoming', ''

            if not live_finished_at:
                live_status = 'is_live'
            else:
                live_status = 'was_live'
                payload = {'broadcast_type': 'dvr'}

                video_allow_dvr_flg = traverse_obj(data_json, ('video', 'allow_dvr_flg'))
                video_convert_to_vod_flg = traverse_obj(data_json, ('video', 'convert_to_vod_flg'))

                self.write_debug(f'allow_dvr_flg = {video_allow_dvr_flg}, convert_to_vod_flg = {video_convert_to_vod_flg}.')

                if not (video_allow_dvr_flg and video_convert_to_vod_flg):
                    raise ExtractorError(
                        'Live was ended, there is no video for download.', video_id=content_code, expected=True)
        else:
            raise ExtractorError(f'Unknown type: {video_type}', video_id=content_code, expected=False)

        self.write_debug(f'{content_code}: video_type={video_type}, live_status={live_status}')

        session_id = self._call_api(
            f'video_pages/{content_code}/session_ids', item_id=f'{content_code}/session',
            data=json.dumps(payload).encode('ascii'), headers={
                'Content-Type': 'application/json',
                'fc_use_device': 'null',
                'origin': 'https://nicochannel.jp',
            },
            note='Getting session id', errnote='Unable to get session id',
        )['data']['session_id']

        return live_status, session_id