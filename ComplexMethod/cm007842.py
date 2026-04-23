def _player_js_cache_key(self, player_url, extra_id=None, _cache={}):
        if player_url not in _cache:
            player_id = self._extract_player_info(player_url)
            player_path = remove_start(
                compat_urllib_parse.urlparse(player_url).path,
                '/s/player/{0}/'.format(player_id))
            variant = next((k for k, v in self._PLAYER_JS_VARIANT_MAP
                           if v == player_path), None)
            if not variant:
                variant = next(
                    (k for k, v in self._PLAYER_JS_VARIANT_MAP
                     if re.match(re.escape(v).replace('en_US', r'\w+') + '$', player_path)),
                    None)
            if not variant:
                self.write_debug(
                    'Unable to determine player JS variant\n'
                    '        player = {0}'.format(player_url), only_once=True)
                variant = re.sub(r'[^a-zA-Z0-9]', '_', remove_end(player_path, '.js'))
            _cache[player_url] = join_nonempty(player_id, variant)

        if extra_id:
            extra_id = '-'.join((_cache[player_url], extra_id))
            assert os.path.basename(extra_id) == extra_id
            return extra_id
        return _cache[player_url]