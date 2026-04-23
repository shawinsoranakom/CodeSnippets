def _insert_cache(self, records, values):
        if not self.translate:
            super()._insert_cache(records, values)
            return

        assert self not in records.env._field_depends_context, f"translated field {self} cannot depend on context"
        env = records.env
        field_cache = env.transaction.field_data[self]
        if env.context.get('prefetch_langs'):
            installed = [lang for lang, _ in env['res.lang'].get_installed()]
            langs = OrderedSet[str](installed + ['en_US'])
            u_langs: list[str] = [f'_{lang}' for lang in langs] if self.translate is not True and env._lang.startswith('_') else []
            for id_, val in zip(records._ids, values):
                if val is None:
                    field_cache.setdefault(id_, None)
                else:
                    if u_langs:  # fallback missing _lang to lang if exists
                        val.update({f'_{k}': v for k, v in val.items() if k in langs and f'_{k}' not in val})
                    field_cache[id_] = {
                        **dict.fromkeys(langs, val['en_US']),  # fallback missing lang to en_US
                        **dict.fromkeys(u_langs, val.get('_en_US')),  # fallback missing _lang to _en_US
                        **val
                    }
        else:
            lang = self.translation_lang(env)
            for id_, val in zip(records._ids, values):
                if val is None:
                    field_cache.setdefault(id_, None)
                else:
                    cache_value = field_cache.setdefault(id_, {})
                    if cache_value is not None:
                        cache_value.setdefault(lang, val)