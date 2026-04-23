def _preload_views(self, refs: Sequence[int | str]) -> dict[int | str, dict]:
        """
        Return self's arch combined with its inherited views archs.

        :param refs: list of id or xmlid
        :return: dictionary of preloaded information {id or xmlid: {xmlid, ref, view, error}}
        """
        self._clear_preload_views_cache_if_needed()

        context = {k: self.env.context.get(k) for k in self.env['ir.qweb']._get_template_cache_keys()}
        cache_key = tuple(context.values())

        compile_batch = self.env.cr.cache.setdefault('_compile_batch_', {}).setdefault(cache_key, {})

        refs = [int(ref) if isinstance(ref, int) or ref.isdigit() else ref for ref in refs]
        missing_refs = [ref for ref in refs if ref and ref not in compile_batch]
        if not missing_refs:
            return compile_batch

        unknown_views = self._fetch_template_views(missing_refs)

        # add in cache
        for id_or_xmlid, view in unknown_views.items():
            if isinstance(view, models.BaseModel):
                compile_batch[view.id] = compile_batch[id_or_xmlid] = {
                    'xmlid': view.key or id_or_xmlid,
                    'ref': view.id,
                    'view': view,
                    'error': False,
                }
            else:
                compile_batch[id_or_xmlid] = {
                    'xmlid': id_or_xmlid,
                    'view': None,
                    'ref': None,
                    'error': view,  # MissingError
                }

        return compile_batch