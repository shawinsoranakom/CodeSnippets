def _extract_event(self, event_data):
        event_id = compat_str(event_data['id'])
        account_id = compat_str(event_data['owner_account_id'])
        feed_root_url = self._API_URL_TEMPLATE % (account_id, event_id) + '/feed.json'

        stream_info = event_data.get('stream_info')
        if stream_info:
            return self._extract_stream_info(stream_info)

        last_video = None
        entries = []
        for i in itertools.count(1):
            if last_video is None:
                info_url = feed_root_url
            else:
                info_url = '{root}?&id={id}&newer=-1&type=video'.format(
                    root=feed_root_url, id=last_video)
            videos_info = self._download_json(
                info_url, event_id, 'Downloading page {0}'.format(i))['data']
            videos_info = [v['data'] for v in videos_info if v['type'] == 'video']
            if not videos_info:
                break
            for v in videos_info:
                v_id = compat_str(v['id'])
                entries.append(self.url_result(
                    'http://livestream.com/accounts/%s/events/%s/videos/%s' % (account_id, event_id, v_id),
                    'Livestream', v_id, v.get('caption')))
            last_video = videos_info[-1]['id']
        return self.playlist_result(entries, event_id, event_data['full_name'])