def _get_relation_chain(self, searched_field_name):
        self.ensure_one()
        if (
            not searched_field_name
            or not searched_field_name in self._fields
            or not self[searched_field_name]
            or not self.model_id
        ):
            return [], ""
        path = self[searched_field_name].split('.')
        if not path:
            return [], ""
        model = self.env[self.model_id.model]
        chain = []
        for field_name in path:
            is_last_field = field_name == path[-1]
            field = model._fields[field_name]
            if not is_last_field:
                if not field.relational:
                    # sanity check: this should be the last field in the path
                    current_field = field.get_description(self.env)["string"]
                    searched_field = self._fields[searched_field_name].get_description(self.env)["string"]
                    raise ValidationError(_("The path contained by the field '%(searched_field)s' contains a non-relational field (%(current_field)s) that is not the last field in the path. You can't traverse non-relational fields (even in the quantum realm). Make sure only the last field in the path is non-relational.", searched_field=searched_field, current_field=current_field))
                model = self.env[field.comodel_name]
            chain.append(field)
        stringified_path = ' > '.join([field.get_description(self.env)["string"] for field in chain])
        return chain, stringified_path