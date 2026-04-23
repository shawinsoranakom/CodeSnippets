def _generate_event_playlist(self, event_data):
        event_id = str(event_data['id'])
        account_id = str(event_data['owner_account_id'])
        feed_root_url = self._API_URL_TEMPLATE % (account_id, event_id) + '/feed.json'

        stream_info = event_data.get('stream_info')
        if stream_info:
            return self._extract_stream_info(stream_info)

        last_video = None
        for i in itertools.count(1):
            if last_video is None:
                info_url = feed_root_url
            else:
                info_url = f'{feed_root_url}?&id={last_video}&newer=-1&type=video'
            videos_info = self._download_json(
                info_url, event_id, f'Downloading page {i}')['data']
            videos_info = [v['data'] for v in videos_info if v['type'] == 'video']
            if not videos_info:
                break
            for v in videos_info:
                v_id = str(v['id'])
                yield self.url_result(
                    f'http://livestream.com/accounts/{account_id}/events/{event_id}/videos/{v_id}',
                    LivestreamIE, v_id, v.get('caption'))
            last_video = videos_info[-1]['id']