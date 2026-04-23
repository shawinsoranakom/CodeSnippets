def _validate_tag_button(self, node, name_manager, node_info):
        if not node_info['validate']:
            return
        name = node.get('name')
        special = node.get('special')
        type_ = node.get('type')
        if special:
            if special not in ('cancel', 'save', 'add'):
                self._raise_view_error(_("Invalid special '%(value)s' in button", value=special), node)
        elif type_:
            if type_ != 'action' and type_ != 'object':
                return
            elif not name:
                return
            elif type_ == 'object':
                func = getattr(name_manager.model, name, None)
                if not func:
                    msg = _(
                        "%(action_name)s is not a valid action on %(model_name)s",
                        action_name=name, model_name=name_manager.model._name,
                    )
                    self._raise_view_error(msg, node)
                # get_public_method(name_manager.model, name) is too slow for this validation, a more naive check is acceptable.
                if name.startswith('_') or (hasattr(func, '_api_private') and func._api_private):
                    msg = _(
                        "%(method)s on %(model)s is private and cannot be called from a button",
                        method=name, model=name_manager.model._name,
                    )
                    self._raise_view_error(msg, node)
                try:
                    inspect.signature(func).bind()
                except TypeError:
                    msg = "%s on %s has parameters and cannot be called from a button"
                    self._log_view_warning(msg % (name, name_manager.model._name), node)
            elif type_ == 'action':
                name_manager.must_exist_action(name, node)

            name_manager.has_action(name)

        if node.get('icon'):
            description = 'A button with icon attribute (%s)' % node.get('icon')
            self._validate_fa_class_accessibility(node, description)