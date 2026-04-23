def _search_model_id(self, operator, value):
        if operator in Domain.NEGATIVE_OPERATORS:
            return NotImplemented
        models = self.env['ir.model']
        if isinstance(value, str):
            models = models.search(Domain('display_name', operator, value))
        elif isinstance(value, Domain):
            models = models.search(value)
        elif operator == 'any!':
            models = models.sudo().search(Domain('id', operator, value))
        elif operator == 'any' or isinstance(value, int):
            models = models.search(Domain('id', operator, value))
        elif operator == 'in':
            models = models.search(Domain.OR(
                Domain('id' if isinstance(v, int) else 'display_name', operator, v)
                for v in value
                if v
            ))
        return Domain('model', 'in', models.mapped('model'))