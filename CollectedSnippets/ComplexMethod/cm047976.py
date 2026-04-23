def _register_hook(self):
        """ Patch models that should trigger action rules based on creation,
            modification, deletion of records and form onchanges.
        """
        #
        # Note: the patched methods must be defined inside another function,
        # otherwise their closure may be wrong. For instance, the function
        # create refers to the outer variable 'create', which you expect to be
        # bound to create itself. But that expectation is wrong if create is
        # defined inside a loop; in that case, the variable 'create' is bound to
        # the last function defined by the loop.
        #

        def make_create():
            """ Instanciate a create method that processes automation rules. """
            @api.model_create_multi
            def create(self, vals_list, **kw):
                # retrieve the automation rules to possibly execute
                automations = self.env['base.automation']._get_actions(self, CREATE_TRIGGERS)
                if not automations:
                    return create.origin(self, vals_list, **kw)
                # call original method
                records = create.origin(self.with_env(automations.env), vals_list, **kw)
                # check postconditions, and execute actions on the records that satisfy them
                for automation in automations.with_context(old_values=None):
                    _logger.debug(
                        "Processing automation rule %s (#%s) on %s records (create)",
                        automation.sudo().name, automation.sudo().id, len(records),
                    )
                    automation._process(automation._filter_post(records, feedback=True))
                return records.with_env(self.env)

            return create

        def make_write():
            """ Instanciate a write method that processes automation rules. """
            def write(self, vals, **kw):
                # retrieve the automation rules to possibly execute
                automations = self.env['base.automation']._get_actions(self, WRITE_TRIGGERS)
                if not (automations and self):
                    return write.origin(self, vals, **kw)
                records = self.with_env(automations.env).filtered('id')
                # check preconditions on records
                pre = {a: a._filter_pre(records) for a in automations}
                # read old values before the update
                old_values = {
                    record.id: {field_name: record[field_name] for field_name in vals if field_name in record._fields and record._fields[field_name].store}
                    for record in records
                }
                # call original method
                write.origin(self.with_env(automations.env), vals, **kw)
                # check postconditions, and execute actions on the records that satisfy them
                for automation in automations.with_context(old_values=old_values):
                    _logger.debug(
                        "Processing automation rule %s (#%s) on %s records (write)",
                        automation.sudo().name, automation.sudo().id, len(records),
                    )
                    records, domain_post = automation._filter_post_export_domain(pre[automation], feedback=True)
                    automation._process(records, domain_post=domain_post)
                return True

            return write

        def make_compute_field_value():
            """ Instanciate a compute_field_value method that processes automation rules. """
            #
            # Note: This is to catch updates made by field recomputations.
            #
            def _compute_field_value(self, field):
                # determine fields that may trigger an automation
                stored_fnames = [f.name for f in self.pool.field_computed[field] if f.store]
                if not stored_fnames:
                    return _compute_field_value.origin(self, field)
                # retrieve the action rules to possibly execute
                automations = self.env['base.automation']._get_actions(self, WRITE_TRIGGERS)
                records = self.filtered('id').with_env(automations.env)
                if not (automations and records):
                    _compute_field_value.origin(self, field)
                    return True
                # check preconditions on records
                # changed fields are all fields computed by the function
                changed_fields = [f for f in records._fields.values() if f.compute == field.compute]
                pre = {a: a.with_context(changed_fields=changed_fields)._filter_pre(records) for a in automations}
                # read old values before the update
                old_values = {
                    record.id: {fname: record[fname] for fname in stored_fnames}
                    for record in records
                }
                # call original method
                _compute_field_value.origin(self, field)
                # check postconditions, and execute automations on the records that satisfy them
                for automation in automations.with_context(old_values=old_values):
                    _logger.debug(
                        "Processing automation rule %s (#%s) on %s records (_compute_field_value)",
                        automation.sudo().name, automation.sudo().id, len(records),
                    )
                    records, domain_post = automation._filter_post_export_domain(pre[automation], feedback=True)
                    automation._process(records, domain_post=domain_post)
                return True

            return _compute_field_value

        def make_unlink():
            """ Instanciate an unlink method that processes automation rules. """
            def unlink(self, **kwargs):
                # retrieve the action rules to possibly execute
                automations = self.env['base.automation']._get_actions(self, ['on_unlink'])
                records = self.with_env(automations.env)
                # check conditions, and execute actions on the records that satisfy them
                for automation in automations:
                    _logger.debug(
                        "Processing automation rule %s (#%s) on %s records (unlink)",
                        automation.sudo().name, automation.sudo().id, len(records),
                    )
                    automation._process(automation._filter_post(records, feedback=True))
                # call original method
                return unlink.origin(self, **kwargs)

            return unlink

        def make_onchange(automation_rule_id):
            """ Instanciate an onchange method for the given automation rule. """
            def base_automation_onchange(self):
                automation_rule = self.env['base.automation'].browse(automation_rule_id)

                if not automation_rule._filter_post(self):
                    # Do nothing if onchange record does not satisfy the filter_domain
                    return

                result = {}
                actions = automation_rule.sudo().action_server_ids.with_context(
                    active_model=self._name,
                    active_id=self._origin.id,
                    active_ids=self._origin.ids,
                    onchange_self=self,
                )
                for action in actions:
                    try:
                        res = action.run()
                    except Exception as e:
                        automation_rule._add_postmortem(e)
                        raise

                    if res:
                        if 'value' in res:
                            res['value'].pop('id', None)
                            self.update({key: val for key, val in res['value'].items() if key in self._fields})
                        if 'domain' in res:
                            result.setdefault('domain', {}).update(res['domain'])
                        if 'warning' in res:
                            result['warning'] = res["warning"]
                return result

            return base_automation_onchange

        def make_message_post():
            def _message_post(self, *args, **kwargs):
                message = _message_post.origin(self, *args, **kwargs)
                # Don't execute automations for a message emitted during
                # the run of automations for a real message
                # Don't execute if we know already that a message is only internal
                message_sudo = message.sudo().with_context(active_test=False)
                if "__action_done"  in self.env.context or message_sudo.is_internal or message_sudo.subtype_id.internal:
                    return message
                if message_sudo.message_type in ('notification', 'auto_comment', 'user_notification'):
                    return message

                # always execute actions when the author is a customer
                # if author is not set, it means the message is coming from outside
                mail_trigger = "on_message_received" if not message_sudo.author_id or message_sudo.author_id.partner_share else "on_message_sent"
                automations = self.env['base.automation']._get_actions(self, [mail_trigger])
                for automation in automations.with_context(old_values=None):
                    records = automation._filter_pre(self, feedback=True)
                    _logger.debug(
                        "Processing automation rule %s (#%s) on %s records (_message_post)",
                        automation.sudo().name, automation.sudo().id, len(records),
                    )
                    automation._process(records)

                return message
            return _message_post

        patched_models = defaultdict(set)

        def patch(model, name, method):
            """ Patch method `name` on `model`, unless it has been patched already. """
            if model not in patched_models[name]:
                patched_models[name].add(model)
                ModelClass = model.env.registry[model._name]
                method.origin = getattr(ModelClass, name)
                setattr(ModelClass, name, method)

        # retrieve all actions, and patch their corresponding model
        for automation_rule in self.with_context({}).search([]):
            Model = self.env.get(automation_rule.model_name)

            # Do not crash if the model of the base_action_rule was uninstalled
            if Model is None:
                _logger.warning(
                    "Automation rule with name '%s' (ID %d) depends on model %s (ID: %d)",
                    automation_rule.name,
                    automation_rule.id,
                    automation_rule.model_name,
                    automation_rule.model_id.id)
                continue

            if automation_rule.trigger in CREATE_WRITE_SET:
                if automation_rule.trigger in CREATE_TRIGGERS:
                    patch(Model, 'create', make_create())
                if automation_rule.trigger in WRITE_TRIGGERS:
                    patch(Model, 'write', make_write())
                    patch(Model, '_compute_field_value', make_compute_field_value())

            elif automation_rule.trigger == 'on_unlink':
                patch(Model, 'unlink', make_unlink())

            elif automation_rule.trigger == 'on_change':
                # register an onchange method for the automation_rule
                method = make_onchange(automation_rule.id)
                for field in automation_rule.on_change_field_ids:
                    Model._onchange_methods[field.name].append(method)

            if automation_rule.model_id.is_mail_thread and automation_rule.trigger in MAIL_TRIGGERS:
                patch(Model, "message_post", make_message_post())