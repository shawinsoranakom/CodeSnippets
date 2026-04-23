def _get_view_fields(self, view_type, models):
        """ Returns the field names required by the web client to load the views according to the view type.

        The method is meant to be overridden by modules extending web client features and requiring additional
        fields.

        :param string view_type: type of the view
        :param dict models: dict holding the models and fields used in the view architecture.
        :return: dict holding the models and field required by the web client given the view type.
        :rtype: list
        """
        if view_type in ('kanban', 'list', 'form'):
            for model, model_fields in models.items():
                model_fields.add('id')
                if 'write_date' in self.env[model]._fields:
                    model_fields.add('write_date')
        elif view_type == 'search':
            models[self._name] = list(self._fields.keys())
        elif view_type == 'graph':
            models[self._name].union(fname for fname, field in self._fields.items() if field.type in ('integer', 'float'))
        elif view_type == 'pivot':
            models[self._name].union(fname for fname, field in self._fields.items() if field._description_groupable(self.env))
        return models