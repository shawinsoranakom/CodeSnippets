def _extract_video_metadata(self, url, video_id, season_id):
        url, smuggled_data = unsmuggle_url(url, {})
        if smuggled_data.get('title'):
            return smuggled_data

        webpage = self._download_webpage(url, video_id)
        # Bstation layout
        initial_data = (
            self._search_json(r'window\.__INITIAL_(?:DATA|STATE)__\s*=', webpage, 'preload state', video_id, default={})
            or self._search_nuxt_data(webpage, video_id, '__initialState', fatal=False, traverse=None))
        video_data = traverse_obj(
            initial_data, ('OgvVideo', 'epDetail'), ('UgcVideo', 'videoData'), ('ugc', 'archive'), expected_type=dict) or {}

        if season_id and not video_data:
            # Non-Bstation layout, read through episode list
            season_json = self._call_api(f'/web/v2/ogv/play/episodes?season_id={season_id}&platform=web', video_id)
            video_data = traverse_obj(season_json, (
                'sections', ..., 'episodes', lambda _, v: str(v['episode_id']) == video_id,
            ), expected_type=dict, get_all=False)

        # XXX: webpage metadata may not accurate, it just used to not crash when video_data not found
        return merge_dicts(
            self._parse_video_metadata(video_data), {
                'title': get_element_by_class(
                    'bstar-meta__title', webpage) or self._html_search_meta('og:title', webpage),
                'description': get_element_by_class(
                    'bstar-meta__desc', webpage) or self._html_search_meta('og:description', webpage),
            }, self._search_json_ld(webpage, video_id, default={}))