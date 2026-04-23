def _construct_player_url(self, *, player_id=None, player_url=None):
        assert player_id or player_url, '_construct_player_url must take one of player_id or player_url'
        if not player_id:
            player_id = self._extract_player_info(player_url)

        force_player_id = False
        player_id_override = self._get_player_js_version()[1]
        if player_id_override and player_id_override != player_id:
            force_player_id = f'Forcing player {player_id_override} in place of player {player_id}'
            player_id = player_id_override

        variant = self._configuration_arg('player_js_variant', [''])[0] or self._DEFAULT_PLAYER_JS_VARIANT
        if variant not in (*self._PLAYER_JS_VARIANT_MAP, 'actual'):
            self.report_warning(
                f'Invalid player JS variant name "{variant}" requested. '
                f'Valid choices are: {", ".join(self._PLAYER_JS_VARIANT_MAP)}', only_once=True)
            variant = self._DEFAULT_PLAYER_JS_VARIANT

        if not player_url:
            if force_player_id:
                self.write_debug(force_player_id, only_once=True)
            if variant == 'actual':
                # We don't have an actual variant so we always use 'main' & don't need to write debug
                variant = 'main'
            return urljoin('https://www.youtube.com', f'/s/player/{player_id}/{self._PLAYER_JS_VARIANT_MAP[variant]}')

        actual_variant = self._get_player_id_variant_and_path(player_url)[1]
        if not force_player_id and (variant == 'actual' or variant == actual_variant):
            return urljoin('https://www.youtube.com', player_url)

        if variant == 'actual':
            if actual_variant:
                variant = actual_variant
            else:
                # We need to force player_id but can't determine variant; fall back to 'main' variant
                variant = 'main'

        self.write_debug(join_nonempty(
            force_player_id,
            variant != actual_variant and f'Forcing "{variant}" player JS variant for player {player_id}',
            f'original url = {player_url}',
            delim='\n        '), only_once=True)

        return urljoin('https://www.youtube.com', f'/s/player/{player_id}/{self._PLAYER_JS_VARIANT_MAP[variant]}')