def get_catalog(self):
        pdict = {}
        catalog = {}
        translation = self.translation
        seen_keys = set()
        while True:
            for key, value in translation._catalog.items():
                if key == "" or key in seen_keys:
                    continue
                if isinstance(key, str):
                    catalog[key] = value
                elif isinstance(key, tuple):
                    msgid, cnt = key
                    pdict.setdefault(msgid, {})[cnt] = value
                else:
                    raise TypeError(key)
                seen_keys.add(key)
            if translation._fallback:
                translation = translation._fallback
            else:
                break

        num_plurals = self._num_plurals
        for k, v in pdict.items():
            catalog[k] = [v.get(i, "") for i in range(num_plurals)]
        return catalog