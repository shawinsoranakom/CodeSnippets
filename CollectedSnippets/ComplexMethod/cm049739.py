def _compute_res_ids(self):
        """ Computation may come from parent in comment mode, if set. It takes
        the parent message's res_id. Otherwise the composer uses the 'active_ids'
        context key, unless it is too big to be stored in database. Indeed
        when invoked for big mailings, 'active_ids' may be a very big list.
        Support of 'active_ids' when sending is granted in order to not always
        rely on 'res_ids' field. When 'active_ids' is not present, fallback
        on 'active_id'. """
        for composer in self.filtered(lambda composer: not composer.res_ids):
            if composer.parent_id and composer.composition_mode == 'comment':
                composer.res_ids = f"{[composer.parent_id.res_id]}"
            else:
                active_res_ids = parse_res_ids(self.env.context.get('active_ids'), self.env)
                # beware, field is limited in storage, usage of active_ids in context still required
                if active_res_ids and len(active_res_ids) <= 500:
                    composer.res_ids = f"{self.env.context['active_ids']}"
                elif not active_res_ids and self.env.context.get('active_id'):
                    composer.res_ids = f"{[self.env.context['active_id']]}"