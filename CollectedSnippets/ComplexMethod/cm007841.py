def _extract_player_url(self, *ytcfgs, **kw_webpage):
        if ytcfgs and not isinstance(ytcfgs[0], dict):
            webpage = kw_webpage.get('webpage') or ytcfgs[0]
        if webpage:
            player_url = self._search_regex(
                r'"(?:PLAYER_JS_URL|jsUrl)"\s*:\s*"([^"]+)"',
                webpage or '', 'player URL', fatal=False)
            if player_url:
                ytcfgs = ytcfgs + ({'PLAYER_JS_URL': player_url},)
        player_url = traverse_obj(
            ytcfgs, (Ellipsis, 'PLAYER_JS_URL'), (Ellipsis, 'WEB_PLAYER_CONTEXT_CONFIGS', Ellipsis, 'jsUrl'),
            get_all=False, expected_type=self._yt_urljoin)

        requested_js_variant = self.get_param('youtube_player_js_variant')
        variant_js = next(
            (v for k, v in self._PLAYER_JS_VARIANT_MAP if k == requested_js_variant),
            None)
        if variant_js:
            player_id_override = self._get_player_js_version()[1]
            player_id = player_id_override or self._extract_player_info(player_url)
            original_url = player_url
            player_url = self._yt_urljoin(
                '/s/player/{0}/{1}'.format(player_id, variant_js))
            if original_url != player_url:
                self.write_debug(
                    'Forcing "{0}" player JS variant for player {1}\n'
                    '        original url = {2}'.format(
                        requested_js_variant, player_id, original_url),
                    only_once=True)
        elif requested_js_variant != 'actual':
            self.report_warning(
                'Invalid player JS variant name "{0}" requested. '
                'Valid choices are: {1}'.format(
                    requested_js_variant, ','.join(k for k, _ in self._PLAYER_JS_VARIANT_MAP)),
                only_once=True)

        return player_url