def download_and_parse_fragment(url, frag_index, request_data=None, headers=None):
            for retry in RetryManager(self.params.get('fragment_retries'), self.report_retry, frag_index=frag_index):
                try:
                    success = dl_fragment(url, request_data, headers)
                    if not success:
                        return False, None, None, None
                    raw_fragment = self._read_fragment(ctx)
                    try:
                        data = ie.extract_yt_initial_data(video_id, raw_fragment.decode('utf-8', 'replace'))
                    except RegexNotFoundError:
                        data = None
                    if not data:
                        data = json.loads(raw_fragment)
                    live_chat_continuation = try_get(
                        data,
                        lambda x: x['continuationContents']['liveChatContinuation'], dict) or {}

                    func = ((info_dict['protocol'] == 'youtube_live_chat' and parse_actions_live)
                            or (frag_index == 1 and try_refresh_replay_beginning)
                            or parse_actions_replay)
                    return (True, *func(live_chat_continuation))
                except HTTPError as err:
                    retry.error = err
                    continue
            return False, None, None, None