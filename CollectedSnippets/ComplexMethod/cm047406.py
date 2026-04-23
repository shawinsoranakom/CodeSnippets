def get_views(self, views, options=None):
        """ Returns the fields_views of given views, along with the fields of
        the current model, and optionally its filters for the given action.

        The return of the method can only depend on the requested view types,
        access rights (views or other records), view access rules, options,
        context lang and TYPE_view_ref (other context values cannot be used).

        Python expressions contained in views or representing domains (on
        python fields) will be evaluated by the client with all the context
        values as well as the record values it has.

        :param views: list of [view_id, view_type]
        :param dict options: a dict optional boolean flags, set to enable:

            ``toolbar``
                includes contextual actions when loading fields_views
            ``load_filters``
                returns the model's filters
            ``action_id``
                id of the action to get the filters, otherwise loads the global
                filters or the model

        :return: dictionary with fields_views, fields and optionally filters
        """
        options = options or {}
        result = {}

        result['views'] = {
            v_type: self.get_view(
                v_id, v_type,
                **options
            )
            for [v_id, v_type] in views
        }

        models = {}
        for view in result['views'].values():
            for model, model_fields in view.pop('models').items():
                models.setdefault(model, set()).update(model_fields)

        result['models'] = {}

        for model, model_fields in models.items():
            result['models'][model] = {"fields": self.env[model].fields_get(
                allfields=model_fields, attributes=self._get_view_field_attributes()
            )}

        # Add related action information if asked
        if options.get('toolbar'):
            for view in result['views'].values():
                view['toolbar'] = {}

            bindings = self.env['ir.actions.actions'].get_bindings(self._name)
            for action_type, key in (('report', 'print'), ('action', 'action')):
                for action in bindings.get(action_type, []):
                    view_types = (
                        action['binding_view_types'].split(',')
                        if action.get('binding_view_types')
                        else result['views'].keys()
                    )
                    for view_type in view_types:
                        if view_type in result['views']:
                            result['views'][view_type]['toolbar'].setdefault(key, []).append(action)

        if options.get('load_filters') and 'search' in result['views']:
            result['views']['search']['filters'] = self.env['ir.filters'].get_filters(
                self._name, options.get('action_id'), options.get('embedded_action_id'), options.get('embedded_parent_res_id')
            )

        return result