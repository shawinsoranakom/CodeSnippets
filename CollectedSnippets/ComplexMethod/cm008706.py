def _extract_signature_timestamp(self, video_id, player_url, ytcfg=None, fatal=False):
        """
        Extract signatureTimestamp (sts)
        Required to tell API what sig/player version is in use.
        """

        player_sts_override = self._get_player_js_version()[0]
        if player_sts_override:
            return int(player_sts_override)

        sts = traverse_obj(ytcfg, ('STS', {int_or_none}))
        if sts:
            return sts

        if not player_url:
            error_msg = 'Cannot extract signature timestamp without player url'
            if fatal:
                raise ExtractorError(error_msg)
            self.report_warning(error_msg)
            return None

        # TODO: Pass `use_disk_cache=True` when preprocessed player JS cache is solved
        if sts := self._load_player_data_from_cache('sts', player_url):
            return sts

        if code := self._load_player(video_id, player_url, fatal=fatal):
            sts = int_or_none(self._search_regex(
                r'(?:signatureTimestamp|sts)\s*:\s*(?P<sts>[0-9]{5})', code,
                'JS player signature timestamp', group='sts', fatal=fatal))
            if sts:
                # TODO: Pass `use_disk_cache=True` when preprocessed player JS cache is solved
                self._store_player_data_to_cache(sts, 'sts', player_url)

        return sts