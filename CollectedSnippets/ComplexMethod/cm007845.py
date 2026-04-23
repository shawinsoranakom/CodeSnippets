def _post_thread_entries(self, post_thread_renderer):
        post_renderer = try_get(
            post_thread_renderer, lambda x: x['post']['backstagePostRenderer'], dict)
        if not post_renderer:
            return
        # video attachment
        video_renderer = try_get(
            post_renderer, lambda x: x['backstageAttachment']['videoRenderer'], dict)
        video_id = None
        if video_renderer:
            entry = self._video_entry(video_renderer)
            if entry:
                yield entry
        # inline video links
        runs = try_get(post_renderer, lambda x: x['contentText']['runs'], list) or []
        for run in runs:
            if not isinstance(run, dict):
                continue
            ep_url = try_get(
                run, lambda x: x['navigationEndpoint']['urlEndpoint']['url'], compat_str)
            if not ep_url:
                continue
            if not YoutubeIE.suitable(ep_url):
                continue
            ep_video_id = YoutubeIE._match_id(ep_url)
            if video_id == ep_video_id:
                continue
            yield self.url_result(ep_url, ie=YoutubeIE.ie_key(), video_id=video_id)