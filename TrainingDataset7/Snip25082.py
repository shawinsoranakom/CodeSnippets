def setUp(self):
        self._old_language = get_language()
        self._translations = trans_real._translations

        # here we rely on .split() being called inside the _fetch()
        # in trans_real.translation()
        class sideeffect_str(str):
            def split(self, *args, **kwargs):
                res = str.split(self, *args, **kwargs)
                trans_real._translations["en-YY"] = None
                return res

        trans_real._translations = {sideeffect_str("en-XX"): None}