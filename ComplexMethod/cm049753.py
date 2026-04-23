def default_get(self, fields):
        res = super().default_get(fields)
        context = self.env.context
        active_res_ids = parse_res_ids(context.get('active_ids'), self.env)
        if 'res_ids' in fields:
            if active_res_ids and len(active_res_ids) <= self._batch_size:
                res['res_ids'] = f"{context['active_ids']}"
            elif not active_res_ids and context.get('active_id'):
                res['res_ids'] = f"{[context['active_id']]}"
        res_model = context.get('active_model') or context.get('params', {}).get('active_model', False)
        if 'res_model' in fields:
            res['res_model'] = res_model
        return res