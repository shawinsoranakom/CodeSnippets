def load(self, data):
        # Workaround for https://github.com/yt-dlp/yt-dlp/issues/4776
        if not isinstance(data, str):
            return super().load(data)

        morsel = None
        for match in self._COOKIE_PATTERN.finditer(data):
            if match.group('bad'):
                morsel = None
                continue

            key, value = match.group('key', 'val')
            if not self._LEGAL_KEY_RE.fullmatch(key):
                morsel = None
                continue

            is_attribute = False
            if key.startswith('$'):
                key = key[1:]
                is_attribute = True

            lower_key = key.lower()
            if lower_key in self._RESERVED:
                if morsel is None:
                    continue

                if value is None:
                    if lower_key not in self._FLAGS:
                        morsel = None
                        continue
                    value = True
                else:
                    value, _ = self.value_decode(value)
                    # Guard against control characters in quoted attribute values
                    if self._CONTROL_CHARACTER_RE.search(value):
                        # While discarding the entire morsel is not very lenient,
                        # it's better than http.cookies.Morsel raising a CookieError
                        # and it's probably better to err on the side of caution
                        self.pop(morsel.key, None)
                        morsel = None
                        continue

                morsel[key] = value

            elif is_attribute:
                morsel = None

            elif value is not None:
                morsel = self.get(key, http.cookies.Morsel())
                real_value, coded_value = self.value_decode(value)
                # Guard against control characters in quoted cookie values
                if self._CONTROL_CHARACTER_RE.search(real_value):
                    morsel = None
                    continue
                morsel.set(key, real_value, coded_value)
                self[key] = morsel

            else:
                morsel = None