def _traverse_related_sql(self, alias: str, field: Field, query: Query) -> tuple[BaseModel, Field, str]:
        """ Traverse the related `field` and add needed join to the `query`.

        :returns: tuple ``(model, field, alias)``, where ``field`` is the last
            field in the sequence, ``model`` is that field's model, and
            ``alias`` is the model's table alias
        """
        assert field.related and not field.store
        if not (self.env.su or field.compute_sudo or field.inherited):
            raise ValueError(f'Cannot convert {field} to SQL because it is not a sudoed related or inherited field')

        model = self.sudo(self.env.su or field.compute_sudo)
        *path_fnames, last_fname = field.related.split('.')
        for path_fname in path_fnames:
            path_field = model._fields[path_fname]
            if path_field.type != 'many2one':
                raise ValueError(f'Cannot convert {field} (related={field.related}) to SQL because {path_fname} is not a Many2one')
            model, alias = path_field.join(model, alias, query)

        return model, model._fields[last_fname], alias