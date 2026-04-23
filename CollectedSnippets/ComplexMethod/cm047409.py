def check(self, view):
        for name, use in self.used_names.items():
            if (
                name not in self.available_actions
                and name not in self.available_names
                and name not in self.model._fields
                and name not in self.field_info
            ):
                msg = _(
                    "Name or id “%(name_or_id)s” in %(use)s does not exist.",
                    name_or_id=name, use=use,
                )
                view._raise_view_error(msg)
            if name not in self.available_actions and name not in self.available_names:
                msg = _(
                    "Name or id “%(name_or_id)s” in %(use)s must be present in view but is missing.",
                    name_or_id=name, use=use,
                )
                view._raise_view_error(msg)

        for name in self.available_fields:
            if name not in self.model._fields and name not in self.field_info:
                message = _("Field `%(name)s` does not exist", name=name)
                view._raise_view_error(message)

        for name, node in self.must_exist_actions.items():
            # logic mimics /web/action/load behaviour
            action = False
            try:
                action_id = int(name)
            except ValueError:
                model, action_id = view.env['ir.model.data']._xmlid_to_res_model_res_id(name, raise_if_not_found=False)
                if not action_id:
                    msg = _("Invalid xmlid %(xmlid)s for button of type action.", xmlid=name)
                    view._raise_view_error(msg, node)
                if not issubclass(view.pool[model], view.pool['ir.actions.actions']):
                    msg = _(
                        "%(xmlid)s is of type %(xmlid_model)s, expected a subclass of ir.actions.actions",
                        xmlid=name, xmlid_model=model,
                    )
                    view._raise_view_error(msg, node)
            action = view.env['ir.actions.actions'].browse(action_id).exists()
            if not action:
                msg = _(
                    "Action %(action_reference)s (id: %(action_id)s) does not exist for button of type action.",
                    action_reference=name, action_id=action_id,
                )
                view._raise_view_error(msg, node)

        for name, node in self.must_exist_groups.items():
            if self.group_definitions.get_id(name) is None:
                msg = _("The group “%(name)s” defined in view does not exist!", name=name)
                view._log_view_warning(msg, node)

        for name, groups_uses in self.used_fields.items():
            use, node = next(iter(groups_uses.values()))
            if name == 'id':  # always available
                continue
            if "." in name:
                msg = _(
                    "Invalid composed field %(definition)s in %(use)s",
                    definition=name, use=use,
                )
                view._raise_view_error(msg)
            info = self.available_fields[name].get('info')

            if info is None:
                if name in ['false', 'true']:
                    _logger.warning("Using Javascript syntax 'true, 'false' in expressions is deprecated, found %s", name)
                    continue
            elif info.get('select') == 'multi':  # mainly for searchpanel, but can be a generic behaviour.
                msg = _(
                    "Field “%(name)s” used in %(use)s is present in view but is in select multi.",
                    name=name, use=use,
                )
                view._raise_view_error(msg)

        for name, (missing_groups, reasons) in self.get_missing_fields().items():
            message, error_type = self._error_message_group_inconsistency(name, missing_groups, reasons)
            if error_type == 'does_not_exist':
                view._raise_view_error(message)
            elif error_type:
                view._log_view_warning(message, None)