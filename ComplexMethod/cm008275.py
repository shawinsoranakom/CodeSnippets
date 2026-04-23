def _real_extract(self, url):
        video_id = self._match_id(url)
        if video_id.startswith('ser.'):
            param_season = parse_qs(url).get('season', [None])
            param_season = [
                (have_number, int_or_none(v) if have_number else str_or_none(v))
                for have_number, v in
                [(int_or_none(ps) is not None, ps) for ps in param_season]
                if v is not None
            ]
            season_kwargs = {
                k: [v for is_num, v in param_season if is_num is c] or None
                for k, c in
                [('season_titles', False), ('season_numbers', True)]
            }
            return self._extract_series(video_id, **season_kwargs)

        return self._extract_episode(self._call_api_get_tiles(video_id))