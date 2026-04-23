def default_get(self, fields):
        result = super().default_get(fields)

        result['res_model'] = result.get('res_model') or self.env.context.get('active_model')

        if not result.get('res_ids'):
            if not result.get('res_id') and self.env.context.get('active_ids') and len(self.env.context.get('active_ids')) > 1:
                result['res_ids'] = repr(self.env.context.get('active_ids'))
        if not result.get('res_id'):
            if not result.get('res_ids') and self.env.context.get('active_id'):
                result['res_id'] = self.env.context.get('active_id')

        return result