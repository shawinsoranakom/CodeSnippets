def context_get(self):
        # use read() to not read other fields: this must work while modifying
        # the schema of models res.users or res.partner
        try:
            context = self.env.user.read(['lang', 'tz'], load=False)[0]
        except IndexError:
            # user not found, no context information
            return frozendict()
        context.pop('id')

        # ensure lang is set and available
        # context > request > company > english > any lang installed
        langs = [code for code, _ in self.env['res.lang'].get_installed()]
        lang = context.get('lang')
        if lang not in langs:
            lang = request.best_lang if request else None
            if lang not in langs:
                lang = self.env.user.with_context(prefetch_fields=False).company_id.partner_id.lang
                if lang not in langs:
                    lang = DEFAULT_LANG
                    if lang not in langs:
                        lang = langs[0] if langs else DEFAULT_LANG
        context['lang'] = lang

        # ensure uid is set
        context['uid'] = self.env.uid

        return frozendict(context)